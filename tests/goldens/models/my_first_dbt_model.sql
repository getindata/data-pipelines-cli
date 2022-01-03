/*
    Models copied from dbt's "starter project", from repository licensed under Apache-2.0 License:
    https://github.com/dbt-labs/dbt-core/tree/main/core/dbt/include/starter_project/models/example
*/

{{ config(materialized='table') }}

with source_data as (
    select 1 as id
    union all
    select null as id
)

select *
from source_data
