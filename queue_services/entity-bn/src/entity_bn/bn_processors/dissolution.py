# Copyright © 2022 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""File processing rules and actions for the dissolution of a business (SP/GP)."""
import xml.etree.ElementTree as Et
from contextlib import suppress
from http import HTTPStatus

from entity_queue_common.service_utils import QueueException
from flask import current_app
from legal_api.models import Business, Filing, RequestTracker
from legal_api.utils.datetime import datetime
from legal_api.utils.legislation_datetime import LegislationDatetime

from entity_bn.bn_processors import build_input_xml, request_bn_hub
from entity_bn.exceptions import BNException


def process(business: Business, filing: Filing):  # pylint: disable=too-many-branches
    """Process the incoming dissolution request (SP/GP)."""
    if not business.tax_id or len(business.tax_id) != 15:
        raise BNException(f'Business {business.identifier}, ' +
                          'Cannot inform CRA about change of status before receiving Business Number (BN15).')

    max_retry = current_app.config.get('BN_HUB_MAX_RETRY')
    request_trackers = RequestTracker.find_by(business.id,
                                              RequestTracker.ServiceName.BN_HUB,
                                              RequestTracker.RequestType.CHANGE_STATUS,
                                              filing.id)
    if not request_trackers:
        request_tracker = RequestTracker()
        request_tracker.business_id = business.id
        request_tracker.filing_id = filing.id
        request_tracker.request_type = RequestTracker.RequestType.CHANGE_STATUS
        request_tracker.service_name = RequestTracker.ServiceName.BN_HUB
        request_tracker.retry_number = 0
        request_tracker.is_processed = False
    elif (request_tracker := request_trackers.pop()) and not request_tracker.is_processed:
        request_tracker.last_modified = datetime.utcnow()
        request_tracker.retry_number += 1

    if request_tracker.is_processed:
        return

    business_registration_number = business.tax_id[0:9]
    business_program_identifier = business.tax_id[9:11]
    business_program_account_reference_number = business.tax_id[11:15]

    effective_date = LegislationDatetime.as_legislation_timezone(filing.effective_date).strftime('%Y-%m-%d')

    program_account_status_code = {
        'putbackon': '01',  # Will be useful while implementing restore a SP/GP. Keeping it here for now as unsued.
        'dissolution': '02'
    }
    program_account_reason_code = {
        'putbackon': None,
        'dissolution': '105'
    }

    input_xml = build_input_xml('change_status', {
        'retryNumber': str(request_tracker.retry_number),
        'filingId': str(filing.id),
        'programAccountStatusCode': program_account_status_code[filing.filing_type],
        'programAccountReasonCode': program_account_reason_code[filing.filing_type],
        'effectiveDate': effective_date,
        'business': business.json(),
        'businessRegistrationNumber': business_registration_number,
        'businessProgramIdentifier': business_program_identifier,
        'businessProgramAccountReferenceNumber': business_program_account_reference_number
    })

    request_tracker.request_object = input_xml
    status_code, response = request_bn_hub(input_xml)
    if status_code == HTTPStatus.OK:
        with suppress(Et.ParseError):
            root = Et.fromstring(response)
            if root.tag == 'SBNAcknowledgement':
                request_tracker.is_processed = True
    request_tracker.response_object = response
    request_tracker.save()

    if not request_tracker.is_processed:
        if request_tracker.retry_number < max_retry:
            raise BNException(f'Retry number: {request_tracker.retry_number + 1}' +
                              f' for {business.identifier}, TrackerId: {request_tracker.id}.')

        raise QueueException(
            f'Retry exceeded the maximum count for {business.identifier}, TrackerId: {request_tracker.id}.')
