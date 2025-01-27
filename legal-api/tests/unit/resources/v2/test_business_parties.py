# Copyright © 2021 Province of British Columbia
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

"""Tests to assure the business-parties end-point.

Test-Suite to ensure that the /businesses../parties endpoint is working as expected.
"""
import datetime
from http import HTTPStatus

from legal_api.services.authz import STAFF_ROLE
from tests.unit.models import Address, Party, PartyRole, factory_business, factory_party_role
from tests.unit.services.utils import create_header


def test_get_business_parties_one_party_multiple_roles(session, client, jwt):
    """Assert that business parties are returned."""
    # setup
    identifier = 'CP7654321'
    business = factory_business(identifier)
    officer = Party(
        first_name='Connor',
        last_name='Horton',
        middle_initial=''
    )
    officer.save()
    party_role_1 = PartyRole(
        role=PartyRole.RoleTypes.DIRECTOR.value,
        appointment_date=datetime.datetime(2017, 5, 17),
        cessation_date=None,
        party_id=officer.id
    )
    party_role_2 = PartyRole(
        role=PartyRole.RoleTypes.CUSTODIAN.value,
        appointment_date=datetime.datetime(2017, 5, 17),
        cessation_date=None,
        party_id=officer.id
    )
    business.party_roles.append(party_role_1)
    business.party_roles.append(party_role_2)
    business.save()

    # test
    rv = client.get(f'/api/v2/businesses/{identifier}/parties',
                    headers=create_header(jwt, [STAFF_ROLE], identifier)
                    )
    # check
    assert rv.status_code == HTTPStatus.OK
    assert 'parties' in rv.json
    assert len(rv.json['parties']) == 1
    assert len(rv.json['parties'][0]['roles']) == 2


def test_get_business_parties_multiple_parties(session, client, jwt):
    """Assert that business parties are returned."""
    # setup
    identifier = 'CP7654321'
    business = factory_business(identifier)
    officer_1 = Party(
        first_name='Connor',
        last_name='Horton',
        middle_initial=''
    )
    party_role_1 = PartyRole(
        role=PartyRole.RoleTypes.DIRECTOR.value,
        appointment_date=datetime.datetime(2017, 5, 17),
        cessation_date=None,
        party=officer_1
    )
    officer_2 = Party(
        first_name='Abraham',
        last_name='Mason',
        middle_initial=''
    )

    party_role_2 = PartyRole(
        role=PartyRole.RoleTypes.CUSTODIAN.value,
        appointment_date=datetime.datetime(2017, 5, 17),
        cessation_date=None,
        party=officer_2
    )
    business.party_roles.append(party_role_1)
    business.party_roles.append(party_role_2)
    business.save()

    # test
    rv = client.get(f'/api/v2/businesses/{identifier}/parties',
                    headers=create_header(jwt, [STAFF_ROLE], identifier)
                    )
    # check
    assert rv.status_code == HTTPStatus.OK
    assert 'parties' in rv.json
    assert len(rv.json['parties']) == 2
    assert len(rv.json['parties'][0]['roles']) == 1
    assert len(rv.json['parties'][1]['roles']) == 1


def test_get_business_parties_by_role(session, client, jwt):
    """Assert that business parties are returned."""
    # setup
    identifier = 'CP7654321'
    business = factory_business(identifier)
    party_address = Address(city='Test Mailing City', address_type=Address.DELIVERY)
    officer_1 = {
        'firstName': 'Michael',
        'lastName': 'Crane',
        'middleInitial': 'Joe',
        'partyType': 'person',
        'organizationName': ''
    }
    party_role_1 = factory_party_role(
        party_address,
        None,
        officer_1,
        datetime.datetime(2017, 5, 17),
        None,
        PartyRole.RoleTypes.DIRECTOR
    )
    officer_2 = {
        'firstName': 'Connor',
        'lastName': 'Horton',
        'middleInitial': '',
        'partyType': 'person',
        'organizationName': ''
    }
    party_role_2 = factory_party_role(
        party_address,
        None,
        officer_2,
        datetime.datetime(2017, 5, 17),
        None,
        PartyRole.RoleTypes.CUSTODIAN
    )
    business.party_roles.append(party_role_1)
    business.party_roles.append(party_role_2)
    business.save()

    # test
    rv = client.get(f'/api/v2/businesses/{identifier}/parties?role=Custodian',
                    headers=create_header(jwt, [STAFF_ROLE], identifier)
                    )
    # check
    assert rv.status_code == HTTPStatus.OK
    assert 'parties' in rv.json
    assert len(rv.json['parties']) == 1


def test_get_business_parties_by_invalid_role(session, client, jwt):
    """Assert that business parties are returned."""
    # setup
    identifier = 'CP7654321'
    business = factory_business(identifier)
    party_address = Address(city='Test Mailing City', address_type=Address.DELIVERY)
    officer = {
        'firstName': 'Michael',
        'lastName': 'Crane',
        'middleInitial': 'Joe',
        'partyType': 'person',
        'organizationName': ''
    }
    party_role_1 = factory_party_role(
        party_address,
        None,
        officer,
        datetime.datetime(2017, 5, 17),
        None,
        PartyRole.RoleTypes.DIRECTOR
    )
    business.party_roles.append(party_role_1)
    business.save()

    # test
    rv = client.get(f'/api/v2/businesses/{identifier}/parties?role=test',
                    headers=create_header(jwt, [STAFF_ROLE], identifier)
                    )
    # check
    assert rv.status_code == HTTPStatus.OK
    assert rv.json['parties'] == []


def test_get_business_no_parties(session, client, jwt):
    """Assert that business parties are not returned."""
    # setup
    identifier = 'CP7654321'
    factory_business(identifier)

    # test
    rv = client.get(f'/api/v2/businesses/{identifier}/parties',
                    headers=create_header(jwt, [STAFF_ROLE], identifier)
                    )
    # check
    assert rv.status_code == HTTPStatus.OK
    assert rv.json['parties'] == []


def test_get_business_ceased_parties(session, client, jwt):
    """Assert that business parties are not returned."""
    # setup
    identifier = 'CP7654321'
    business = factory_business(identifier)
    officer = {
        'firstName': 'Michael',
        'lastName': 'Crane',
        'middleInitial': 'Joe',
        'partyType': 'person',
        'organizationName': ''
    }
    party_role = factory_party_role(
        None,
        None,
        officer,
        datetime.datetime(2012, 5, 17),
        datetime.datetime(2013, 5, 17),
        PartyRole.RoleTypes.DIRECTOR
    )
    business.party_roles.append(party_role)
    business.save()

    # test
    rv = client.get(f'/api/v2/businesses/{identifier}/parties',
                    headers=create_header(jwt, [STAFF_ROLE], identifier)
                    )
    # check
    assert rv.status_code == HTTPStatus.OK
    assert rv.json['parties'] == []


def test_get_business_party_by_id(session, client, jwt):
    """Assert that business party is returned."""
    # setup
    identifier = 'CP7654321'
    business = factory_business(identifier)
    officer = Party(
        first_name='Connor',
        last_name='Horton',
        middle_initial=''
    )
    officer.save()
    party_role = PartyRole(
        role=PartyRole.RoleTypes.DIRECTOR.value,
        appointment_date=datetime.datetime(2017, 5, 17),
        cessation_date=None,
        party_id=officer.id
    )
    business.party_roles.append(party_role)
    business.save()
    # test
    rv = client.get(f'/api/v2/businesses/{identifier}/parties/{officer.id}',
                    headers=create_header(jwt, [STAFF_ROLE], identifier)
                    )
    # check
    assert rv.status_code == HTTPStatus.OK
    assert rv.json['party'] is not None
    assert len(rv.json['party']['roles']) == 1


def test_get_business_party_by_invalid_id(session, client, jwt):
    """Assert that business party is not returned."""
    # setup
    identifier = 'CP7654321'
    business = factory_business(identifier)
    party_id = 5000
    business.save()

    # test
    rv = client.get(f'/api/v2/businesses/{identifier}/parties/{party_id}',
                    headers=create_header(jwt, [STAFF_ROLE], identifier)
                    )
    # check
    assert rv.status_code == HTTPStatus.NOT_FOUND
    assert rv.json == {'message': f'Party {party_id} not found'}


def test_get_parties_invalid_business(session, client, jwt):
    """Assert that business is not returned."""
    # setup
    identifier = 'CP7654321'

    # test
    rv = client.get(f'/api/v2/businesses/{identifier}/parties',
                    headers=create_header(jwt, [STAFF_ROLE], identifier)
                    )
    # check
    assert rv.status_code == HTTPStatus.NOT_FOUND
    assert rv.json == {'message': f'{identifier} not found'}
