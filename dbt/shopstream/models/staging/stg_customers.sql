with source as (

    select * from {{ source('raw', 'raw_customers') }}

),

-- Drop rows we can't key on, then rank duplicates by email so we can keep
-- just the earliest signup for each address.
ranked as (

    select
        customer_id,
        {{ clean_string('name') }}          as customer_name,
        lower({{ clean_string('email') }})  as email,
        country                             as raw_country,
        signup_date,
        row_number() over (
            partition by lower(email)
            order by signup_date, customer_id
        ) as row_num
    from source
    where email is not null

),

final as (

    select
        customer_id,
        customer_name,
        email,
        -- Collapse the many country spellings down to ISO-2 codes.
        case
            when upper(trim(raw_country)) in ('US', 'USA', 'UNITED STATES') then 'US'
            when upper(trim(raw_country)) in ('UK', 'GB', 'UNITED KINGDOM') then 'GB'
            when upper(trim(raw_country)) in ('IN', 'INDIA')                then 'IN'
            when upper(trim(raw_country)) in ('DE', 'GERMANY')              then 'DE'
            when upper(trim(raw_country)) in ('FR', 'FRANCE')               then 'FR'
            when upper(trim(raw_country)) in ('CA', 'CANADA')               then 'CA'
            when upper(trim(raw_country)) in ('AU', 'AUSTRALIA')            then 'AU'
            else null
        end as country_code,
        signup_date
    from ranked
    where row_num = 1

)

select * from final
