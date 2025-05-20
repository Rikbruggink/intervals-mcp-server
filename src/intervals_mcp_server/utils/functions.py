import httpx
from http import HTTPStatus
import json
from typing import Any
import os


try:
    from dotenv import load_dotenv

    _ = load_dotenv()
except ImportError:
    # python-dotenv not installed, proceed without it
    pass

INTERVALS_API_BASE_URL = os.getenv(
    "INTERVALS_API_BASE_URL", "https://intervals.icu/api/v1"
)

USER_AGENT = "intervalsicu-mcp-server/1.0"


async def make_intervals_request(
    url: str, 
    api_key: str | None = None, 
    params: dict[str, Any] | None = None
) -> dict[str, Any] | list[dict[str, Any]]:
    """Make a GET request to the Intervals.icu API with proper error handling."""

    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    auth = httpx.BasicAuth("API_KEY", api_key)
    full_url = f"{INTERVALS_API_BASE_URL}{url}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                full_url, headers=headers, params=params, auth=auth, timeout=30.0
            )

            # Assign to _ to indicate intentional ignoring of return value
            _ = response.raise_for_status()
            return response.json() if response.content else {}

        except httpx.HTTPStatusError as e:
            error_code = e.response.status_code
            error_text = e.response.text

            logger.error("HTTP error: %s - %s", error_code, error_text)

            # Provide specific messages for common error codes
            error_messages = {
                HTTPStatus.UNAUTHORIZED: f"{HTTPStatus.UNAUTHORIZED.value} {HTTPStatus.UNAUTHORIZED.phrase}: Please check your API key.",
                HTTPStatus.FORBIDDEN: f"{HTTPStatus.FORBIDDEN.value} {HTTPStatus.FORBIDDEN.phrase}: You may not have permission to access this resource.",
                HTTPStatus.NOT_FOUND: f"{HTTPStatus.NOT_FOUND.value} {HTTPStatus.NOT_FOUND.phrase}: The requested endpoint or ID doesn't exist.",
                HTTPStatus.UNPROCESSABLE_ENTITY: f"{HTTPStatus.UNPROCESSABLE_ENTITY.value} {HTTPStatus.UNPROCESSABLE_ENTITY.phrase}: The server couldn't process the request (invalid parameters or unsupported operation).",
                HTTPStatus.TOO_MANY_REQUESTS: f"{HTTPStatus.TOO_MANY_REQUESTS.value} {HTTPStatus.TOO_MANY_REQUESTS.phrase}: Too many requests in a short time period.",
                HTTPStatus.INTERNAL_SERVER_ERROR: f"{HTTPStatus.INTERNAL_SERVER_ERROR.value} {HTTPStatus.INTERNAL_SERVER_ERROR.phrase}: The Intervals.icu server encountered an internal error.",
                HTTPStatus.SERVICE_UNAVAILABLE: f"{HTTPStatus.SERVICE_UNAVAILABLE.value} {HTTPStatus.SERVICE_UNAVAILABLE.phrase}: The Intervals.icu server might be down or undergoing maintenance.",
            }

            # Get a specific message or default to the server's response
            try:
                status = HTTPStatus(error_code)
                custom_message = error_messages.get(status, error_text)
            except ValueError:
                # If the status code doesn't map to HTTPStatus, use the error_text
                custom_message = error_text

            return {"error": True, "status_code": error_code, "message": custom_message}
        except httpx.RequestError as e:
            logger.error("Request error: %s", str(e))
            return {"error": True, "message": f"Request error: {str(e)}"}
        except Exception as e:
            logger.error("Unexpected error: %s", str(e))
            return {"error": True, "message": f"Unexpected error: {str(e)}"}


async def post_intervals_data(
    data, url: str, 
    api_key: str | None = None, 
    params: dict[str, Any] | None = None
) -> dict[str, Any] | list[dict[str, Any]]:
    """Make a POST request to the Intervals.icu API with proper error handling."""

    headers = {"User-Agent": USER_AGENT, "Accept": "application/json", "Content-Type": "application/json"}

    auth = httpx.BasicAuth("API_KEY", api_key)
    full_url = f"{INTERVALS_API_BASE_URL}{url}"
    final_data=json.dumps(data)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                full_url, headers=headers, params=params, auth=auth, timeout=30.0, data=final_data
            )

            # Assign to _ to indicate intentional ignoring of return value
            _ = response.raise_for_status()
            return response.json() if response.content else {}

        except httpx.HTTPStatusError as e:
            error_code = e.response.status_code
            error_text = e.response.text

            logger.error("HTTP error: %s - %s", error_code, error_text)

            # Provide specific messages for common error codes
            error_messages = {
                HTTPStatus.UNAUTHORIZED: f"{HTTPStatus.UNAUTHORIZED.value} {HTTPStatus.UNAUTHORIZED.phrase}: Please check your API key.",
                HTTPStatus.FORBIDDEN: f"{HTTPStatus.FORBIDDEN.value} {HTTPStatus.FORBIDDEN.phrase}: You may not have permission to access this resource.",
                HTTPStatus.NOT_FOUND: f"{HTTPStatus.NOT_FOUND.value} {HTTPStatus.NOT_FOUND.phrase}: The requested endpoint or ID doesn't exist.",
                HTTPStatus.UNPROCESSABLE_ENTITY: f"{HTTPStatus.UNPROCESSABLE_ENTITY.value} {HTTPStatus.UNPROCESSABLE_ENTITY.phrase}: The server couldn't process the request (invalid parameters or unsupported operation).",
                HTTPStatus.TOO_MANY_REQUESTS: f"{HTTPStatus.TOO_MANY_REQUESTS.value} {HTTPStatus.TOO_MANY_REQUESTS.phrase}: Too many requests in a short time period.",
                HTTPStatus.INTERNAL_SERVER_ERROR: f"{HTTPStatus.INTERNAL_SERVER_ERROR.value} {HTTPStatus.INTERNAL_SERVER_ERROR.phrase}: The Intervals.icu server encountered an internal error.",
                HTTPStatus.SERVICE_UNAVAILABLE: f"{HTTPStatus.SERVICE_UNAVAILABLE.value} {HTTPStatus.SERVICE_UNAVAILABLE.phrase}: The Intervals.icu server might be down or undergoing maintenance.",
            }

            # Get a specific message or default to the server's response
            try:
                status = HTTPStatus(error_code)
                custom_message = error_messages.get(status, error_text)
            except ValueError:
                # If the status code doesn't map to HTTPStatus, use the error_text
                custom_message = error_text

            return {"error": True, "status_code": error_code, "message": custom_message}
        except httpx.RequestError as e:
            logger.error("Request error: %s", str(e))
            return {"error": True, "message": f"Request error: {str(e)}"}
        except Exception as e:
            logger.error("Unexpected error: %s", str(e))
            return {"error": True, "message": f"Unexpected error: {str(e)}"}