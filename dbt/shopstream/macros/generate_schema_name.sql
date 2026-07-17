{#
    By default dbt builds models into <target_schema>_<custom_schema>
    (e.g. STAGING_STAGING), which is ugly. This override uses the custom
    schema name as-is, so models land in the STAGING and MARTS schemas we
    already created in snowflake/02_setup_schemas.sql.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim | upper }}
    {%- endif -%}
{%- endmacro %}
