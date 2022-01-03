/*
    Models copied from dbt's "starter project", from repository licensed under Apache-2.0 License:
    https://github.com/dbt-labs/dbt-core/tree/main/core/dbt/include/starter_project/models/example
*/

select *
from {{ ref('my_first_dbt_model') }}
where id = 1
