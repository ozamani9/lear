def get_unprocessed_firms_query():
    query = f"""
            select tbl_fe.*, cp.flow_name, cp.processed_status
            from (select e.corp_num,
                         count(e.corp_num)                         as cnt,
                         string_agg(e.event_type_cd || '_' || COALESCE(f.filing_type_cd, 'NULL'), ', '
                                    order by e.event_id)           as event_file_types,
                         array_agg(e.event_id order by e.event_id) as event_ids,
                         min(e.event_id)                           as first_event_id
                  from event e
                           left outer join filing f on e.event_id = f.event_id
                  where 1 = 1
                  group by e.corp_num) as tbl_fe
                     left outer join corp_processing cp on cp.corp_num = tbl_fe.corp_num and cp.flow_name = 'sp-gp-flow'
            where 1 = 1
             and tbl_fe.event_file_types like 'FILE_FRREG%'
              and (cp.processed_status is null or cp.processed_status <> 'COMPLETED')
            order by tbl_fe.first_event_id
            limit 100
            ;
        """
    return query


def get_firm_event_filing_data_query(corp_num: str, event_id: int):
    query = f"""
        select
            -- event
            e.event_id             as e_event_id,
            e.corp_num             as e_corp_num,
            e.event_type_cd        as e_event_type_cd,
            e.trigger_dts          as e_trigger_dts,
            -- filing
            f.event_id             as f_event_id,
            f.filing_type_cd       as f_filing_type_cd,
            TO_TIMESTAMP(to_char(f.effective_dt, 'YYYY-MM-DD'), 'YYYY-MM-DD') as f_effective_dts,
            f.withdrawn_event_id   as f_withdrawn_event_id,
            f.ods_type_cd          as f_ods_type,
            f.nr_num               as f_nr_num,
            -- corporation
            c.corp_num             as c_corp_num,
            c.corp_frozen_type_cd  as c_corp_frozen_type_cd,
            c.corp_type_cd         as c_corp_type_cd,
            TO_TIMESTAMP(to_char(c.recognition_dts, 'YYYY-MM-DD'), 'YYYY-MM-DD') as c_recognition_dts,
            c.bn_9                 as c_bn_9,
            c.bn_15                as c_bn_15,
            c.admin_email          as c_admin_email,
            -- corp_name
            cn.corp_num            as cn_corp_num,
            cn.corp_name_typ_cd    as cn_corp_name_typ_cd,
            cn.start_event_id      as cn_start_event_id,
            cn.end_event_id        as cn_end_event_id,
            cn.corp_name           as cn_corp_name,
            -- corp_state
            cs.corp_num            as cs_corp_num,
            cs.start_event_id      as cs_start_event_id,
            cs.end_event_id        as cs_end_event_id,
            cs.state_type_cd       as cs_corp_state_typ_cd,
            -- business_description
            bd.corp_num            as bd_corp_num,
            bd.start_event_id      as bd_start_event_id,
            bd.end_event_id        as bd_end_event_id,
            TO_TIMESTAMP(to_char(bd.business_start_date, 'YYYY-MM-DD'), 'YYYY-MM-DD') as bd_business_start_date,
            bd.naics_code          as bd_naics_code,
            bd.description         as bd_description,
            -- ledger_text
            lt.event_id            as lt_event_id,
            lt.notation            as lt_notation,
            -- payment
            p.event_id             as p_event_id,
            p.payment_typ_cd       as payment_typ_cd,
            p.fee_cd               as p_fee_cd,
            p.gst_num              as p_gst_num,
            p.bcol_account_num     as p_bcol_account_num,
            p.payment_total        as p_payment_total,
            p.folio_num            as p_folio_num,
            p.dat_num              as p_dat_num,
            p.routing_slip         as p_routing_slip,
            p.fas_balance          as p_fas_balance,
            -- filing user
            u.event_id             as u_event_id,
            u.user_id              as u_user_id,
            u.last_name            as u_last_name,
            u.first_name           as u_first_name,
            u.middle_name          as u_middle_name,
            u.email_addr           as u_email_addr
        from event e
                 left outer join filing f on e.event_id = f.event_id
                 left outer join corporation c on c.corp_num = e.corp_num
                 left outer join corp_name cn on cn.start_event_id = e.event_id
                 left outer join corp_state cs on cs.start_event_id = e.event_id
                 left outer join business_description bd on bd.start_event_id = e.event_id
                 left outer join ledger_text lt on lt.event_id = e.event_id
                 left outer join payment p on p.event_id = e.event_id
                 left outer join filing_user u on u.event_id = e.event_id
        where 1 = 1
          and e.corp_num = '{corp_num}'
          and e.event_id = {event_id}
        order by e.event_id
        ;
        """
    return query


def get_firm_event_filing_corp_party_data_query(corp_num: str, event_id: int):
    query = f"""
        select cp.corp_party_id                                                     as cp_corp_party_id,
               cp.mailing_addr_id                                                   as cp_mailing_addr_id,
               cp.delivery_addr_id                                                  as cp_delivery_addr_id,
               cp.corp_num                                                          as cp_corp_num,
               cp.party_typ_cd                                                      as cp_party_typ_cd,
               cp.start_event_id                                                    as cp_start_event_id,
               cp.end_event_id                                                      as cp_end_event_id,
               cp.prev_party_id                                                     as cp_prev_party_id,
               TO_CHAR(cp.appointment_dt, 'YYYY-MM-DD')                             as cp_appointment_dt,
               cp.last_name              as cp_last_name,
               cp.middle_name            as cp_middle_name,
               cp.first_name             as cp_first_name,
               cp.business_name          as cp_business_name,
               NULLIF(cp.bus_company_num, '')                                       as cp_bus_company_num,
               cp.email_address          as cp_email_address,
               cp.phone                  as cp_phone,
               -- mailing address
               ma.addr_id                as ma_addr_id,
               ma.province               as ma_province,
               ma.country_typ_cd         as ma_country_typ_cd,
               ma.postal_cd              as ma_postal_cd,
               ma.addr_line_1            as ma_addr_line_1,
               ma.addr_line_2            as ma_addr_line_2,
               ma.addr_line_3            as ma_addr_line_3,
               ma.city                   as ma_city,
               ma.address_format_type    as ma_address_format_type,
               ma.delivery_instructions  as ma_delivery_instructions,
               ma.unit_no                as ma_unit_no,
               ma.unit_type              as ma_unit_type,
               ma.civic_no               as ma_civic_no,
               ma.civic_no_suffix        as ma_civic_no_suffix,
               ma.street_name            as ma_street_name,
               ma.street_type            as ma_street_type,
               ma.street_direction       as ma_street_direction,
               ma.lock_box_no            as ma_lock_box_no,
               ma.installation_type      as ma_installation_type,
               ma.installation_name      as ma_installation_name,
               ma.installation_qualifier as ma_installation_qualifier,
               ma.route_service_type     as ma_route_service_type,
               ma.route_service_no       as ma_route_service_no,
               -- delivery address
               da.addr_id                as da_addr_id,
               da.province               as da_province,
               da.country_typ_cd         as da_country_typ_cd,
               da.postal_cd              as da_postal_cd,
               da.addr_line_1            as da_addr_line_1,
               da.addr_line_2            as da_addr_line_2,
               da.addr_line_3            as da_addr_line_3,
               da.city                   as da_city,
               da.address_format_type    as da_address_format_type,
               da.delivery_instructions  as da_delivery_instructions,
               da.unit_no                as da_unit_no,
               da.unit_type              as da_unit_type,
               da.civic_no               as da_civic_no,
               da.civic_no_suffix        as da_civic_no_suffix,
               da.street_name            as da_street_name,
               da.street_type            as da_street_type,
               da.street_direction       as da_street_direction,
               da.lock_box_no            as da_lock_box_no,
               da.installation_type      as da_installation_type,
               da.installation_name      as da_installation_name,
               da.installation_qualifier as da_installation_qualifier,
               da.route_service_type     as da_route_service_type,
               da.route_service_no       as da_route_service_no
        from event e
                 join corp_party cp on cp.start_event_id = e.event_id
                 left outer join address ma on cp.mailing_addr_id = ma.addr_id
                 left outer join address da on cp.delivery_addr_id = da.addr_id
        where 1 = 1
          and e.corp_num = '{corp_num}'
          and e.event_id = {event_id}
        order by e.event_id
        ;
        """
    return query


def get_firm_event_filing_office_data_query(corp_num: str, event_id: int):
    query = f"""
        select o.corp_num                as o_corp_num,
               o.office_typ_cd           as o_office_typ_cd,
               o.start_event_id          as o_start_event_id,
               o.end_event_id            as o_end_event_id,
               o.mailing_addr_id         as o_mailing_addr_id,
               o.delivery_addr_id        as o_delivery_addr_id,
               -- mailing address
               ma.addr_id                as ma_addr_id,
               ma.province               as ma_province,
               ma.country_typ_cd         as ma_country_typ_cd,
               ma.postal_cd              as ma_postal_cd,
               ma.addr_line_1            as ma_addr_line_1,
               ma.addr_line_2            as ma_addr_line_2,
               ma.addr_line_3            as ma_addr_line_3,
               ma.city                   as ma_city,
               ma.address_format_type    as ma_address_format_type,
               ma.delivery_instructions  as ma_delivery_instructions,
               ma.unit_no                as ma_unit_no,
               ma.unit_type              as ma_unit_type,
               ma.civic_no               as ma_civic_no,
               ma.civic_no_suffix        as ma_civic_no_suffix,
               ma.street_name            as ma_street_name,
               ma.street_type            as ma_street_type,
               ma.street_direction       as ma_street_direction,
               ma.lock_box_no            as ma_lock_box_no,
               ma.installation_type      as ma_installation_type,
               ma.installation_name      as ma_installation_name,
               ma.installation_qualifier as ma_installation_qualifier,
               ma.route_service_type     as ma_route_service_type,
               ma.route_service_no       as ma_route_service_no,
               -- delivery address
               da.addr_id                as da_addr_id,
               da.province               as da_province,
               da.country_typ_cd         as da_country_typ_cd,
               da.postal_cd              as da_postal_cd,
               da.addr_line_1            as da_addr_line_1,
               da.addr_line_2            as da_addr_line_2,
               da.addr_line_3            as da_addr_line_3,
               da.city                   as da_city,
               da.address_format_type    as da_address_format_type,
               da.delivery_instructions  as da_delivery_instructions,
               da.unit_no                as da_unit_no,
               da.unit_type              as da_unit_type,
               da.civic_no               as da_civic_no,
               da.civic_no_suffix        as da_civic_no_suffix,
               da.street_name            as da_street_name,
               da.street_type            as da_street_type,
               da.street_direction       as da_street_direction,
               da.lock_box_no            as da_lock_box_no,
               da.installation_type      as da_installation_type,
               da.installation_name      as da_installation_name,
               da.installation_qualifier as da_installation_qualifier,
               da.route_service_type     as da_route_service_type,
               da.route_service_no       as da_route_service_no
        from event e
                 join office o on o.start_event_id = e.event_id
                 left outer join address ma on o.mailing_addr_id = ma.addr_id
                 left outer join address da on o.delivery_addr_id = da.addr_id
        where 1 = 1
          and e.corp_num = '{corp_num}'
          and e.event_id = {event_id}
        ;
        """
    return query
