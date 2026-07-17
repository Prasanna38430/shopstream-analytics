{#
    Trim whitespace and turn empty strings into proper NULLs. Handy across
    the staging models where source text can be blank or padded.
#}
{% macro clean_string(column_name) -%}
    nullif(trim({{ column_name }}), '')
{%- endmacro %}
