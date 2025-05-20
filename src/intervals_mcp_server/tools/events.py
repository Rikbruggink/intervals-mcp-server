from server import mcp
from datetime import datetime, timedelta
from config.defaults import settings

from utils.functions import (
    make_intervals_request,
    post_intervals_data
)

from utils.formatting import (
    format_event_details,
    format_event_summary
)

@mcp.tool()
async def get_events(
    athlete_id: str | None = None,
    api_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None
) -> str:
    """
    
    Get events for an athlete from Intervals.icu

    Args:
        athlete_id: The Intervals.icu athlete ID
        api_key: The Intervals.icu API key
        start_date: Start date in YYYY-MM-DD
        end_date: End date in YYYY-MM-DD format

    Returns:
        Planned events from Intervals.icu for further processing

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
        start_date = datetime.now().strftime("%Y-%m-%d")
    if not end_date:
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    # Call the Intervals.icu API
    params = {"oldest": start_date, "newest": end_date}

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/events", api_key=api_key_to_use, params=params
    )

    if isinstance(result, dict) and "error" in result:
        error_message = result.get("message", "Unknown error")
        return f"Error fetching events: {error_message}"

    # Format the response
    if not result:
        return f"No events found for athlete {athlete_id_to_use} in the specified date range."

    # Ensure result is a list
    events = result if isinstance(result, list) else []

    if not events:
        return f"No events found for athlete {athlete_id_to_use} in the specified date range."

    events_summary = "Events:\n\n"
    for event in events:
        if not isinstance(event, dict):
            continue

        events_summary += format_event_summary(event) + "\n\n"

    return events_summary

@mcp.tool()
async def get_event_by_id(
    event_id: str,
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Get detailed information for a specific event from Intervals.icu

    Args:
        event_id: The Intervals.icu event ID
        athlete_id: The Intervals.icu athlete ID
        api_key: The Intervals.icu API key
    """
    # Use provided athlete_id or fall back to global ATHLETE_ID
    athlete_id_to_use = athlete_id if athlete_id is not None else settings.ATHLETE_ID
    if not athlete_id_to_use:
        return "Error: No athlete ID provided and no default ATHLETE_ID found in environment variables."
    
    # Use provided api_key or fall back to global API_KEY
    api_key_to_use = api_key if api_key is not None else settings.API_KEY
    if not api_key_to_use:
        return "Error: No api_key provided and no default API_KEY found in environment variables."
    
    # Call the Intervals.icu API
    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/event/{event_id}", api_key=api_key_to_use
    )

    if isinstance(result, dict) and "error" in result:
        error_message = result.get("message", "Unknown error")
        return f"Error fetching event details: {error_message}"

    # Format the response
    if not result:
        return f"No details found for event {event_id}."

    if not isinstance(result, dict):
        return f"Invalid event format for event {event_id}."

    return format_event_details(result)

def convert_duration(duration):
    if "km" in duration:
        return float(duration.replace("km", "")) * 1000  # Convert km to meters
    elif "m" in duration and not duration.endswith("km"):
        return int(duration.replace("m", "")) * 60  # Convert minutes to seconds
    elif "s" in duration:
        return int(duration.replace("s", ""))  # Keep seconds as is
    else:
        return int(duration)  # Default for unknown formats

# Expand repeated intervals into separate blocks
def expand_repeats(steps):
    expanded_steps = []
    for step in steps:
        if "description" in step and step["description"].endswith("x"):
            repeat_count = int(step["description"].replace("x", "").strip())
            for _ in range(repeat_count):
                expanded_steps.extend(steps[steps.index(step) + 1:steps.index(step) + 3])
        elif "duration" in step:
            expanded_steps.append(step)
    return expanded_steps

@mcp.tool()
async def post_events(
    athlete_id: str | None = None,
    api_key: str | None = None,
    start_date: str | None = None,
    name: str | None = None,
    data: dict | None = None,

) -> str:
    """Post events for an athlete to Intervals.icu this follows the event api from intervals.icu as listed 
    in https://intervals.icu/api-docs.html#post-/api/v1/athlete/-id-/events

    An example used from https://github.com/h3xh0und/intervals.icu-api/blob/main/upload_training.py how to format the data for percentage of ftp in power
        {
            "start_date": "2025-01-14",
            "name": "Run - VO2 Max Intervals",
            "steps": [
                {"duration": "15m", "power": "80%",  "description": "Warm-up"},
                {"duration": "3m", "power": "110%",  "description": "High-intensity interval"},
                {"duration": "3m", "power": "80%",  "description": "Recovery"},
                {"duration": "3m", "power": "110%",  "description": "High-intensity interval"},
                {"duration": "10m", "power": "80%", "description": "Cool-down"}
            ]
        }

    Args:
        athlete_id: The Intervals.icu athlete ID (optional, will use ATHLETE_ID from .env if not provided)
        api_key: The Intervals.icu API key (optional, will use API_KEY from .env if not provided)
        start_date: Start date in YYYY-MM-DD format (optional, defaults to today)
        name: Name of the activity
        description: General description of the workout to post.
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
        start_date = datetime.now().strftime("%Y-%m-%d")

    description_lines = []
    expanded_steps = data["steps"]

    for step in expanded_steps:
        description_lines.append(f"- {step['duration']} {step['power']}")
        if "cadence" in step:
            description_lines[-1] += f" ({step['cadence']})"

    final_data = {}

    final_data.update({
            "start_date_local": start_date + "T00:00:00",
            "category": "WORKOUT",
            "name": name,
            "description": "\n".join(description_lines).strip(),
            "type": "Ride" if "Bike" in name else "Run" if "Run" in name else "Swim",
            "target": "POWER" if "Power" in name else "PACE" if "pace" in name else "HR" if "hr" in name else "AUTO",
            "moving_time": sum(
                convert_duration(step["duration"]) for step in expanded_steps
            ),
        })
    
    # Call the Intervals.icu API

    result = await post_intervals_data(
        url=f"/athlete/{athlete_id_to_use}/events", api_key=api_key_to_use, data=final_data
    )

    if isinstance(result, dict) and "error" in result:
        error_message = result.get("message", "Unknown error")
        return f"Error fetching events: {error_message}" f" data used:{final_data}"

    # Format the response
    if not result:
        return f"No events posted for athlete {athlete_id}."


    # Ensure result is a dict
    events = result if isinstance(result, dict) else []

    if not events:
        return f"format error, verify intervals for correct event at {start_date}"

    return events