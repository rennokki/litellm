"""
Main File for Fine Tuning API implementation

https://platform.openai.com/docs/api-reference/fine-tuning

- fine_tuning.jobs.create()
- fine_tuning.jobs.list()
- client.fine_tuning.jobs.list_events()
"""

import asyncio
import contextvars
import os
from functools import partial
from typing import Any, Coroutine, Dict, Literal, Optional, Union

import httpx

import litellm
from litellm.llms.openai_fine_tuning.openai import (
    FineTuningJob,
    FineTuningJobCreate,
    OpenAIFineTuningAPI,
)
from litellm.types.llms.openai import Hyperparameters
from litellm.types.router import *
from litellm.utils import supports_httpx_timeout

####### ENVIRONMENT VARIABLES ###################
openai_fine_tuning_instance = OpenAIFineTuningAPI()
#################################################


async def acreate_fine_tuning_job(
    model: str,
    training_file: str,
    hyperparameters: Optional[Hyperparameters] = {},
    suffix: Optional[str] = None,
    validation_file: Optional[str] = None,
    integrations: Optional[List[str]] = None,
    seed: Optional[int] = None,
    custom_llm_provider: Literal["openai"] = "openai",
    extra_headers: Optional[Dict[str, str]] = None,
    extra_body: Optional[Dict[str, str]] = None,
    **kwargs,
) -> FineTuningJob:
    """
    Async: Creates and executes a batch from an uploaded file of request

    LiteLLM Equivalent of POST: https://api.openai.com/v1/batches
    """
    try:
        loop = asyncio.get_event_loop()
        kwargs["acreate_fine_tuning_job"] = True

        # Use a partial function to pass your keyword arguments
        func = partial(
            create_fine_tuning_job,
            model,
            training_file,
            hyperparameters,
            suffix,
            validation_file,
            integrations,
            seed,
            custom_llm_provider,
            extra_headers,
            extra_body,
            **kwargs,
        )

        # Add the context to the function
        ctx = contextvars.copy_context()
        func_with_context = partial(ctx.run, func)
        init_response = await loop.run_in_executor(None, func_with_context)
        if asyncio.iscoroutine(init_response):
            response = await init_response
        else:
            response = init_response  # type: ignore
        return response
    except Exception as e:
        raise e


def create_fine_tuning_job(
    model: str,
    training_file: str,
    hyperparameters: Optional[Hyperparameters] = {},
    suffix: Optional[str] = None,
    validation_file: Optional[str] = None,
    integrations: Optional[List[str]] = None,
    seed: Optional[int] = None,
    custom_llm_provider: Literal["openai"] = "openai",
    extra_headers: Optional[Dict[str, str]] = None,
    extra_body: Optional[Dict[str, str]] = None,
    **kwargs,
) -> Union[FineTuningJob, Coroutine[Any, Any, FineTuningJob]]:
    """
    Creates a fine-tuning job which begins the process of creating a new model from a given dataset.

    Response includes details of the enqueued job including job status and the name of the fine-tuned models once complete

    """
    try:
        optional_params = GenericLiteLLMParams(**kwargs)
        if custom_llm_provider == "openai":

            # for deepinfra/perplexity/anyscale/groq we check in get_llm_provider and pass in the api base from there
            api_base = (
                optional_params.api_base
                or litellm.api_base
                or os.getenv("OPENAI_API_BASE")
                or "https://api.openai.com/v1"
            )
            organization = (
                optional_params.organization
                or litellm.organization
                or os.getenv("OPENAI_ORGANIZATION", None)
                or None  # default - https://github.com/openai/openai-python/blob/284c1799070c723c6a553337134148a7ab088dd8/openai/util.py#L105
            )
            # set API KEY
            api_key = (
                optional_params.api_key
                or litellm.api_key  # for deepinfra/perplexity/anyscale we check in get_llm_provider and pass in the api key from there
                or litellm.openai_key
                or os.getenv("OPENAI_API_KEY")
            )
            ### TIMEOUT LOGIC ###
            timeout = (
                optional_params.timeout or kwargs.get("request_timeout", 600) or 600
            )
            # set timeout for 10 minutes by default

            if (
                timeout is not None
                and isinstance(timeout, httpx.Timeout)
                and supports_httpx_timeout(custom_llm_provider) == False
            ):
                read_timeout = timeout.read or 600
                timeout = read_timeout  # default 10 min timeout
            elif timeout is not None and not isinstance(timeout, httpx.Timeout):
                timeout = float(timeout)  # type: ignore
            elif timeout is None:
                timeout = 600.0

            _is_async = kwargs.pop("acreate_fine_tuning_job", False) is True

            create_fine_tuning_job_data = FineTuningJobCreate(
                model=model,
                training_file=training_file,
                hyperparameters=hyperparameters,
                suffix=suffix,
                validation_file=validation_file,
                integrations=integrations,
                seed=seed,
            )

            response = openai_fine_tuning_instance.create_fine_tuning_job(
                api_base=api_base,
                api_key=api_key,
                organization=organization,
                create_fine_tuning_job_data=create_fine_tuning_job_data,
                timeout=timeout,
                max_retries=optional_params.max_retries,
                _is_async=_is_async,
            )
        else:
            raise litellm.exceptions.BadRequestError(
                message="LiteLLM doesn't support {} for 'create_batch'. Only 'openai' is supported.".format(
                    custom_llm_provider
                ),
                model="n/a",
                llm_provider=custom_llm_provider,
                response=httpx.Response(
                    status_code=400,
                    content="Unsupported provider",
                    request=httpx.Request(method="create_thread", url="https://github.com/BerriAI/litellm"),  # type: ignore
                ),
            )
        return response
    except Exception as e:
        raise e