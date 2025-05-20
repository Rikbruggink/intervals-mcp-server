from server import mcp
from datetime import datetime, timedelta
from typing import Any

from utils.formatting import (
    format_activity_summary,
    format_intervals,
)
from utils.functions import make_intervals_request

from config.defaults import settings




@mcp.tool()
async def get_activities(
    athlete_id: str | None = None,
    api_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 10,
    include_unnamed: bool = False,
) -> str:
    """Get a list of activities for an athlete from Intervals.icu

    Args:
        athlete_id: The Intervals.icu athlete ID (optional, will use ATHLETE_ID from .env if not provided)
        api_key: The Intervals.icu API key (optional, will use API_KEY from .env if not provided)
        start_date: Start date in YYYY-MM-DD format (optional, defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (optional, defaults to today)
        limit: Maximum number of activities to return (optional, defaults to 10)
        include_unnamed: Whether to include unnamed activities (optional, defaults to False)
    """
    # Use provided athlete_id or fall back to global ATHLETE_ID
    athlete_id_to_use = athlete_id if athlete_id is not None else settings.ATHLETE_ID
    if not athlete_id_to_use:
        return "Error: No athlete ID provided and no default ATHLETE_ID found in environment variables."
    
    # Use provided api_key or fall back to global API_KEY
    api_key_to_use = api_key if api_key is not None else settings.API_KEY
    if not api_key_to_use:
        return "Error: No api_key provided and no default API_KEY found in environment variables."

    # Parse date parameters
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # Fetch more activities if we need to filter out unnamed ones
    api_limit = limit * 3 if not include_unnamed else limit

    # Call the Intervals.icu API
    params = {"oldest": start_date, "newest": end_date, "limit": api_limit}

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/activities", api_key=api_key_to_use, params=params
    )

    # Check for error differently based on result type
    if isinstance(result, dict) and "error" in result:
        error_message = result.get("message", "Unknown error")
        return f"Error fetching activities: {error_message}"

    # Format the response
    if not result:
        return f"No activities found for athlete {athlete_id_to_use} in the specified date range."

    # Ensure result is a list of activity dictionaries
    activities: list[dict[str, Any]] = []

    if isinstance(result, list):
        # Result is already a list
        activities = [item for item in result if isinstance(item, dict)]
    elif isinstance(result, dict):
        # Result is a single activity or a container
        for key, value in result.items():
            if isinstance(value, list):
                # Found a list inside the dictionary
                activities = [item for item in value if isinstance(item, dict)]
                break
        # If no list was found but the dict has typical activity fields, treat it as a single activity
        if not activities and any(
            key in result for key in ["name", "startTime", "distance"]
        ):
            activities = [result]

    if not activities:
        return f"No valid activities found for athlete {athlete_id_to_use} in the specified date range."

    # Filter out unnamed activities if needed and limit to requested count
    if not include_unnamed:
        activities = [
            activity
            for activity in activities
            if activity.get("name") and activity.get("name") != "Unnamed"
        ]

        # If we don't have enough named activities, try to fetch more
        if len(activities) < limit:
            # Calculate how far back we need to go to get more activities
            oldest_date = datetime.fromisoformat(start_date)
            older_start_date = (oldest_date - timedelta(days=60)).strftime("%Y-%m-%d")
            older_end_date = (oldest_date - timedelta(days=1)).strftime("%Y-%m-%d")

            # Additional fetch if needed
            if older_start_date < older_end_date:
                more_params = {
                    "oldest": older_start_date,
                    "newest": older_end_date,
                    "limit": api_limit,
                }
                more_result = await make_intervals_request(
                    url=f"/athlete/{athlete_id_to_use}/activities",
                    api_key=api_key_to_use,
                    params=more_params,
                )

                if isinstance(more_result, list):
                    more_activities = [
                        activity
                        for activity in more_result
                        if isinstance(activity, dict)
                        and activity.get("name")
                        and activity.get("name") != "Unnamed"
                    ]
                    activities.extend(more_activities)

    # Limit to requested count
    activities = activities[:limit]

    if not activities:
        if include_unnamed:
            return f"No valid activities found for athlete {athlete_id_to_use} in the specified date range."
        else:
            return f"No named activities found for athlete {athlete_id_to_use} in the specified date range. Try with include_unnamed=True to see all activities."

    activities_summary = "Activities:\n\n"
    for activity in activities:
        if isinstance(activity, dict):
            activities_summary += format_activity_summary(activity) + "\n"
        else:
            activities_summary += f"Invalid activity format: {activity}\n\n"

    return activities_summary


@mcp.tool()
async def get_activity_details(activity_id: str, api_key: str | None = None) -> str:
    """Get detailed information for a specific activity from Intervals.icu

    Args:
        activity_id: The Intervals.icu activity ID
        api_key: The Intervals.icu API key (optional, will use API_KEY from .env if not provided)
    """
    
    # Use provided api_key or fall back to global API_KEY
    api_key_to_use = api_key if api_key is not None else settings.API_KEY
    if not api_key_to_use:
        return "Error: No api_key provided and no default API_KEY found in environment variables."
    
    # Call the Intervals.icu API
    result = await make_intervals_request(
        url=f"/activity/{activity_id}", api_key=api_key_to_use
    )

    if isinstance(result, dict) and "error" in result:
        error_message = result.get("message", "Unknown error")
        return f"Error fetching activity details: {error_message}"

    # Format the response
    if not result:
        return f"No details found for activity {activity_id}."

    # If result is a list, use the first item if available
    activity_data = result[0] if isinstance(result, list) and result else result
    if not isinstance(activity_data, dict):
        return f"Invalid activity format for activity {activity_id}."

    # Return a more detailed view of the activity
    detailed_view = format_activity_summary(activity_data)

    # Add additional details if available
    if "zones" in activity_data:
        zones = activity_data["zones"]
        detailed_view += "\nPower Zones:\n"
        for zone in zones.get("power", []):
            detailed_view += (
                f"Zone {zone.get('number')}: {zone.get('secondsInZone')} seconds\n"
            )

        detailed_view += "\nHeart Rate Zones:\n"
        for zone in zones.get("hr", []):
            detailed_view += (
                f"Zone {zone.get('number')}: {zone.get('secondsInZone')} seconds\n"
            )

    return detailed_view

@mcp.tool()
async def get_activity_intervals(activity_id: str, api_key: str | None = None) -> str:
    """Get interval data for a specific activity from Intervals.icu

    This endpoint returns detailed metrics for each interval in an activity, including power, heart rate,
    cadence, speed, and environmental data. It also includes grouped intervals if applicable.

    Args:
        activity_id: The Intervals.icu activity ID
        api_key: The Intervals.icu API key (optional, will use API_KEY from .env if not provided)
    """
    
    # Use provided api_key or fall back to global API_KEY
    api_key_to_use = api_key if api_key is not None else settings.API_KEY
    if not api_key_to_use:
        return "Error: No api_key provided and no default API_KEY found in environment variables."
    # Call the Intervals.icu API
    result = await make_intervals_request(
        url=f"/activity/{activity_id}/intervals", api_key=api_key_to_use
    )

    if isinstance(result, dict) and "error" in result:
        error_message = result.get("message", "Unknown error")
        return f"Error fetching intervals: {error_message}"

    # Format the response
    if not result:
        return f"No interval data found for activity {activity_id}."

    # If the result is empty or doesn't contain expected fields
    if not isinstance(result, dict) or not any(
        key in result for key in ["icu_intervals", "icu_groups"]
    ):
        return f"No interval data or unrecognized format for activity {activity_id}."

    # Format the intervals data
    return format_intervals(result)