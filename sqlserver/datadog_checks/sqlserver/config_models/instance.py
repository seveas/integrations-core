# (C) Datadog, Inc. 2021-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

# This file is autogenerated.
# To change this file you should edit assets/configuration/spec.yaml and then run the following commands:
#     ddev -x validate config -s <INTEGRATION_NAME>
#     ddev -x validate models -s <INTEGRATION_NAME>

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from datadog_checks.base.utils.functions import identity
from datadog_checks.base.utils.models import validation

from . import defaults, validators


class Aws(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    instance_endpoint: Optional[str] = None


class Azure(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    deployment_type: Optional[str] = None
    fully_qualified_domain_name: Optional[str] = None


class CollectSettings(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    collection_interval: Optional[float] = None
    enabled: Optional[bool] = None


class CustomQuery(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    columns: Optional[tuple[MappingProxyType[str, Any], ...]] = None
    query: Optional[str] = None
    tags: Optional[tuple[str, ...]] = None


class Gcp(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    instance_id: Optional[str] = None
    project_id: Optional[str] = None


class ManagedIdentity(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    client_id: Optional[str] = None
    identity_scope: Optional[str] = None


class MetricPatterns(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    exclude: Optional[tuple[str, ...]] = None
    include: Optional[tuple[str, ...]] = None


class ObfuscatorOptions(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    collect_commands: Optional[bool] = None
    collect_comments: Optional[bool] = None
    collect_metadata: Optional[bool] = None
    collect_tables: Optional[bool] = None
    keep_sql_alias: Optional[bool] = None
    replace_digits: Optional[bool] = None


class QueryActivity(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    collection_interval: Optional[float] = None
    enabled: Optional[bool] = None


class QueryMetrics(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    collection_interval: Optional[float] = None
    disable_secondary_tags: Optional[bool] = None
    dm_exec_query_stats_row_limit: Optional[int] = None
    enabled: Optional[bool] = None
    enforce_collection_interval_deadline: Optional[bool] = None
    max_queries: Optional[int] = None
    samples_per_hour_per_query: Optional[int] = None


class InstanceConfig(BaseModel):
    model_config = ConfigDict(
        validate_default=True,
        arbitrary_types_allowed=True,
        frozen=True,
    )
    adoprovider: Optional[str] = None
    ao_database: Optional[str] = None
    autodiscovery_db_service_check: Optional[bool] = None
    autodiscovery_exclude: Optional[tuple[str, ...]] = None
    autodiscovery_include: Optional[tuple[str, ...]] = None
    availability_group: Optional[str] = None
    aws: Optional[Aws] = None
    azure: Optional[Azure] = None
    collect_settings: Optional[CollectSettings] = None
    command_timeout: Optional[int] = None
    connection_string: Optional[str] = None
    connector: Optional[str] = None
    custom_queries: Optional[tuple[CustomQuery, ...]] = None
    database: Optional[str] = None
    database_autodiscovery: Optional[bool] = None
    database_autodiscovery_interval: Optional[int] = None
    database_instance_collection_interval: Optional[float] = None
    db_fragmentation_object_names: Optional[tuple[str, ...]] = None
    dbm: Optional[bool] = None
    disable_generic_tags: Optional[bool] = None
    driver: Optional[str] = None
    dsn: Optional[str] = None
    empty_default_hostname: Optional[bool] = None
    gcp: Optional[Gcp] = None
    host: str
    ignore_missing_database: Optional[bool] = None
    include_ao_metrics: Optional[bool] = None
    include_db_file_space_usage_metrics: Optional[bool] = None
    include_db_fragmentation_metrics: Optional[bool] = None
    include_fci_metrics: Optional[bool] = None
    include_instance_metrics: Optional[bool] = None
    include_master_files_metrics: Optional[bool] = None
    include_task_scheduler_metrics: Optional[bool] = None
    log_unobfuscated_plans: Optional[bool] = None
    log_unobfuscated_queries: Optional[bool] = None
    managed_identity: Optional[ManagedIdentity] = None
    metric_patterns: Optional[MetricPatterns] = None
    min_collection_interval: Optional[float] = None
    obfuscator_options: Optional[ObfuscatorOptions] = None
    only_custom_queries: Optional[bool] = None
    only_emit_local: Optional[bool] = None
    password: Optional[str] = None
    proc_only_if: Optional[str] = None
    proc_only_if_database: Optional[str] = None
    query_activity: Optional[QueryActivity] = None
    query_metrics: Optional[QueryMetrics] = None
    reported_hostname: Optional[str] = None
    server_version: Optional[str] = None
    service: Optional[str] = None
    stored_procedure: Optional[str] = None
    tags: Optional[tuple[str, ...]] = None
    use_global_custom_queries: Optional[str] = None
    username: Optional[str] = None

    @model_validator(mode='before')
    def _initial_validation(cls, values):
        return validation.core.initialize_config(getattr(validators, 'initialize_instance', identity)(values))

    @field_validator('*', mode='before')
    def _validate(cls, value, info):
        field = cls.model_fields[info.field_name]
        field_name = field.alias or info.field_name
        if field_name in info.context['configured_fields']:
            value = getattr(validators, f'instance_{info.field_name}', identity)(value, field=field)
        else:
            value = getattr(defaults, f'instance_{info.field_name}', lambda: value)()

        return validation.utils.make_immutable(value)

    @model_validator(mode='after')
    def _final_validation(cls, model):
        return validation.core.check_model(getattr(validators, 'check_instance', identity)(model))
