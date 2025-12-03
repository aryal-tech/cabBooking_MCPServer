"""
Cab Booking MCP Server
A simple MCP server that demonstrates tools, resources, and prompts
"""
import asyncio
import logging
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cab-booking-mcp")

#server initialization
"""
Server: The main MCP server instance
- Handles all incoming requests from Claude Desktop
- Registers tools, resources, and prompts
- Manages the lifecycle of connections
"""

server = Server("cab-booking-mcp")

# Simulated database , mongodb in next phase
bookings_db = {}
booking_counter = 1000

"""
Tools: Actions that Claude can execute
- Defined using @server.list_tools() and @server.call_tool()
- Must have clear names and descriptions
- Use Pydantic models for type safety
"""

class BookCabInput(BaseModel):
    """Input schema for booking a cab"""
    pickup_location: str = Field(description="Pickup location")
    dropoff_location: str = Field(description="Drop-off location")
    pickup_datetime: str = Field(description="Pickup date and time (ISO format)")
    cab_type: str = Field(description="Type of cab (Standard/Premium/Luxury)")

#tools defination
@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    List all available tools
    Claude Desktop calls this to discover what actions are available
    """
    return [
        Tool(
            name="book_cab",
            description="Books a cab with specified details. Returns booking confirmation.",
            inputSchema=BookCabInput.model_json_schema()
        ),
        Tool(
            name="check_booking_status",
            description="Checks the status of a booking by booking ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": "The booking reference ID (e.g., CAB1001)"
                    }
                },
                "required": ["booking_id"]
            }
        ),
        Tool(
            name="list_available_cabs",
            description="Lists all available cabs in a specific area",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location to search for cabs"
                    }
                },
                "required": ["location"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """
    Execute a tool when Claude requests it
    This is called when Claude decides to use one of the tools
    """
    
    if name == "book_cab":
        # Extract arguments
        pickup = arguments["pickup_location"]
        dropoff = arguments["dropoff_location"]
        datetime = arguments["pickup_datetime"]
        cab_type = arguments["cab_type"]
        
        # Create booking
        global booking_counter
        booking_id = f"CAB{booking_counter}"
        booking_counter += 1
        
        # Store in database(simulated db)
        bookings_db[booking_id] = {
            "booking_id": booking_id,
            "pickup_location": pickup,
            "dropoff_location": dropoff,
            "pickup_datetime": datetime,
            "cab_type": cab_type,
            "status": "confirmed",
            "fare": 50.00  # Simplified pricing
        }
        
        # Return confirmation
        return [
            TextContent(
                type="text",
                text=f"""Cab Booking Confirmed!

                        Booking ID: {booking_id}
                        Pickup: {pickup}
                        Drop-off: {dropoff}
                        Time: {datetime}
                        Cab Type: {cab_type}
                        Status: CONFIRMED
                        Estimated Fare: $50.00

                        Your driver details will be sent 30 minutes before pickup.
                        """
            )
        ]
    
    elif name == "check_booking_status":
        booking_id = arguments["booking_id"]
        
        if booking_id in bookings_db:
            booking = bookings_db[booking_id]
            return [
                TextContent(
                    type="text",
                    text=f""" Booking Status

                           Booking ID: {booking['booking_id']}
                           Status: {booking['status'].upper()}
                           Pickup: {booking['pickup_location']}
                           Drop-off: {booking['dropoff_location']}
                           Time: {booking['pickup_datetime']}
                           Cab Type: {booking['cab_type']}
                           Fare: ${booking['fare']}
                        """
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Booking {booking_id} not found. Please check the booking ID."
                )
            ]
    
    elif name == "list_available_cabs":
        location = arguments["location"]
        
        # Simulated available cabs
        available_cabs = [
            {"type": "Standard", "count": 5, "eta": "3 mins"},
            {"type": "Premium", "count": 3, "eta": "5 mins"},
            {"type": "Luxury", "count": 1, "eta": "8 mins"}
        ]
        
        response = f" Available Cabs near {location}:\n\n"
        for cab in available_cabs:
            response += f"• {cab['type']}: {cab['count']} available (ETA: {cab['eta']})\n"
        
        return [
            TextContent(
                type="text",
                text=response
            )
        ]
    
    else:
        return [
            TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )
        ]

#resouce defination (read only)
"""
Resources: Read-only data that Claude can access
- Identified by URI (like URLs)
- Can be static or dynamic
- Used for reference data
"""

@server.list_resources()
async def list_resources() -> list[Any]:
    """
    List all available resources
    Claude can read these but cannot modify them
    """
    return [
        {
            "uri": "booking://all",
            "name": "All Bookings",
            "description": "Complete list of all cab bookings",
            "mimeType": "application/json"
        }
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """
    Read a specific resource by URI
    Called when Claude wants to access resource data
    """
    if uri == "booking://all":
        import json
        return json.dumps(bookings_db, indent=2)
    else:
        raise ValueError(f"Unknown resource: {uri}")

#prompt defination
"""
Prompts: Reusable templates that guide Claude's behavior
- Help maintain consistent responses
- Can have parameters
- Used for common workflows
"""

@server.list_prompts()
async def list_prompts() -> list[Any]:
    """
    List all available prompt templates
    """
    return [
        {
            "name": "booking_assistant",
            "description": "Professional cab booking assistant prompt",
            "arguments": []
        }
    ]


@server.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str] | None = None) -> Any:
    """
    Get a specific prompt template
    """
    if name == "booking_assistant":
        return {
            "messages": [
                {
                    "role": "system",
                    "content": {
                        "type": "text",
                        "text": """You are a professional cab booking assistant.

Guidelines:
- Be friendly and efficient
- Always confirm booking details before finalizing
- Provide clear estimated fares
- Offer alternative cab types if needed
- Handle cancellations professionally

Available cab types:
- Standard: Budget-friendly option
- Premium: Comfortable mid-range
- Luxury: High-end experience
"""
                    }
                }
            ]
        }
    else:
        raise ValueError(f"Unknown prompt: {name}")


#entry point
"""
stdio_server: Standard Input/Output transport
- Runs the server using stdin/stdout
- Claude Desktop communicates via this transport
- Most common transport for local MCP servers
"""

async def main():
    """
    Main entry point
    Starts the MCP server with stdio transport
    """
    logger.info("Starting Cab Booking MCP Server...")
    
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Server running on stdio transport")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())