from fastapi import FastAPI, HTTPException, Query, Path, Depends, Body, Header, Security
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from fastapi.security import APIKeyHeader

import uvicorn
from helpers import KickAPI

app = FastAPI(
    title="Kick.com Unofficial API",
    description="An unofficial API for Kick.com",
    version="1.0.0",
)

kick_api = KickAPI()
session_token_header = APIKeyHeader(name="Authorization", auto_error=False)


class SortOption(str, Enum):
    views = "views"
    date = "date"
    trending = "trending"


class TimeFilter(str, Enum):
    day = "24h"
    week = "7d"
    month = "30d"
    all = "all"

class ErrorResponse(BaseModel):
    detail: str
    status_code: int


class MessageBadge(BaseModel):
    type: str
    text: str
    count: int
    active: bool


class MessageIdentity(BaseModel):
    color: str
    badges: List[MessageBadge]


class MessageSender(BaseModel):
    id: int
    slug: str
    username: str
    identity: MessageIdentity


class ChatMessage(BaseModel):
    id: str
    chat_id: int
    user_id: int
    content: str
    type: str
    metadata: Optional[Any] = None
    created_at: datetime
    sender: MessageSender


class ChatroomInfo(BaseModel):
    id: int
    name: str
    followers_count: int
    subscribers_count: int
    slow_mode: bool
    followers_mode: bool
    subscribers_mode: bool


class UserIdentity(BaseModel):
    id: int
    username: str
    role: str
    badges: List[str] = []
    following_since: Optional[datetime] = None
    subscribed_since: Optional[datetime] = None


class ChatroomRules(BaseModel):
    rules: List[str]
    updated_at: datetime


class Video(BaseModel):
    id: int
    title: str
    url: str
    thumbnail_url: str
    duration: int
    views: int
    created_at: datetime


class Clip(BaseModel):
    id: int
    title: str
    url: str
    thumbnail_url: str
    duration: int
    view_count: int
    created_at: datetime
    broadcaster: Dict[str, Any]


class Category(BaseModel):
    id: int
    name: str
    slug: str
    icon_url: str


def pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
):
    return {"page": page, "per_page": per_page}


async def get_session_token(session_token: str = Security(session_token_header)) -> str:
    """
    Dependency to verify session token exists.
    Returns the session token if valid, raises 401 if missing or invalid format.
    """
    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Session token is required. Format: 'Bearer your-token-here'"
        )
    
    if not session_token.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid session token format. Must start with 'Bearer'"
        )
    
    return session_token


@app.get(
    "/api/v2/channels/{channel_name}/chatroom",
    response_model=Dict[str, Any],
    responses={404: {"model": ErrorResponse}},
)
async def get_chatroom(channel_name: str = Path(..., description="Channel name")):
    """
    Get detailed chatroom information for a specific channel.
    """
    try:
        response = kick_api.send_request(
            f"/api/v2/channels/{channel_name}/chatroom", method="GET"
        )

        if not response.is_success:
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail=f"Channel '{channel_name}' not found"
                )
            raise HTTPException(
                status_code=response.status_code,
                detail=response.error or "Failed to fetch chatroom info",
            )

        return response.data

    except Exception as e:
        print(f"Error fetching chatroom info for channel {channel_name}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching chatroom info"
        )


@app.get(
    "/api/v2/channels/{channel_id}/messages",
    response_model=List[ChatMessage],
    responses={404: {"model": ErrorResponse}},
)
async def get_channel_messages(
    channel_id: int = Path(..., description="Channel ID"),
    start_time: Optional[datetime] = Query(
        None, description="Get messages after this timestamp"
    ),
):
    """
    Retrieve channel messages with support for pagination and time filtering.
    Messages can be filtered to show only those after a specific timestamp.
    """
    try:
        params = {}
        if start_time:
            params["start_time"] = start_time.isoformat()

        response = kick_api.send_request(
            f"/api/v2/channels/{channel_id}/messages", method="GET", json_data=params
        )

        if not response.is_success:
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail=f"Channel '{channel_id}' not found"
                )
            raise HTTPException(
                status_code=response.status_code,
                detail=response.error or "Failed to fetch messages",
            )

        return response.data.get("messages", [])

    except Exception as e:
        print(f"Error fetching messages for channel {channel_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching messages"
        )


@app.get(
    "/api/v2/channels/{channel_id}/users/{user_id}/identity",
    response_model=UserIdentity,
    responses={404: {"model": ErrorResponse}},
)
async def get_user_identity(
    channel_id: int = Path(..., description="Channel ID"),
    user_id: int = Path(..., description="User ID"),
):
    """
    Get detailed user identity information within a specific channel context.
    Includes roles, badges, and subscription status.
    """
    pass


@app.get(
    "/api/v2/channels/{channel_name}/chatroom/rules",
    response_model=Dict[str, str],
    responses={404: {"model": ErrorResponse}},
)
async def get_chatroom_rules(channel_name: str = Path(..., description="Channel name")):
    """
    Retrieve the chatroom rules for a specific channel.
    Returns just the rules if they exist.
    """
    try:
        response = kick_api.send_request(
            f"/api/v2/channels/{channel_name}/chatroom/rules", method="GET"
        )

        if not response.is_success:
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail=f"Channel '{channel_name}' not found"
                )
            raise HTTPException(
                status_code=response.status_code,
                detail=response.error or "Failed to fetch rules",
            )

        rules = response.data.get("data", {}).get("rules")
        if not rules:
            return {"rules": ""}

        return {"rules": rules}

    except Exception as e:
        print(f"Error fetching rules for channel {channel_name}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching rules"
        )


@app.get(
    "/api/v2/channels/{channel_name}/videos",
    response_model=List[Video],
    responses={404: {"model": ErrorResponse}},
)
async def get_channel_videos(
    channel_name: str = Path(..., description="Channel name"),
):
    """
    Get channel videos with support for pagination and category filtering.
    """
    try:
        response = kick_api.send_request(
            f"/api/v2/channels/{channel_name}/videos",
            method="GET",
        )

        if not response.is_success:
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail=f"Channel '{channel_name}' not found"
                )
            raise HTTPException(
                status_code=response.status_code,
                detail=response.error or "Failed to fetch videos",
            )

        videos = []
        for video_data in response.data:
            videos.append(
                Video(
                    id=video_data.get("id"),
                    title=video_data.get("session_title"),
                    url=f"https://kick.com/{channel_name}/video/{video_data.get('id')}",
                    thumbnail_url=video_data.get("thumbnail").get("src"),
                    duration=int(video_data.get("duration"))
                    // 1000,  # Convert from milliseconds to seconds
                    views=video_data.get("views"),
                    created_at=datetime.fromisoformat(
                        video_data.get("created_at").replace("Z", "+00:00")
                    ),
                )
            )

        return videos

    except Exception as e:
        print(f"Error fetching videos for channel {channel_name}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching videos"
        )


@app.get(
    "/api/v2/channels/{channel_name}/clips",
    response_model=List[Dict[str, Any]],
    responses={404: {"model": ErrorResponse}},
)
async def get_channel_clips(
    channel_name: str = Path(..., description="Channel name"),
    sort: SortOption = Query(SortOption.views, description="Sort clips by"),
    time: TimeFilter = Query(TimeFilter.all, description="Time filter for clips"),
):
    """
    Get channel clips with sorting and time filtering options.
    """
    try:
        params = {"sort": sort, "time": time}

        response = kick_api.send_request(
            f"/api/v2/channels/{channel_name}/clips", method="GET", json_data=params
        )

        if not response.is_success:
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail=f"Channel '{channel_name}' not found"
                )
            raise HTTPException(
                status_code=response.status_code,
                detail=response.error or "Failed to fetch clips",
            )

        return response.data.get("clips", [])

    except Exception as e:
        print(f"Error fetching clips for channel {channel_name}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching clips"
        )


@app.get(
    "/api/v2/channels/{channel_name}/recent-categories",
    response_model=List[Dict[str, Any]],
    responses={404: {"model": ErrorResponse}},
)
async def get_recent_categories(
    channel_name: str = Path(..., description="Channel name")
):
    """
    Get recent categories for a channel.
    """
    try:
        response = kick_api.send_request(
            f"/api/v2/channels/{channel_name}/recent-categories", method="GET"
        )

        if not response.is_success:
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail=f"Channel '{channel_name}' not found"
                )
            raise HTTPException(
                status_code=response.status_code,
                detail=response.error or "Failed to fetch recent categories",
            )

        return response.data

    except Exception as e:
        print(f"Error fetching recent categories for channel {channel_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching recent categories",
        )


@app.get(
    "/api/v2/channels/{channel_name}/leaderboards",
    response_model=Dict[str, Any],
    responses={404: {"model": ErrorResponse}},
)
async def get_channel_leaderboards(
    channel_name: str = Path(..., description="Channel name")
):
    """
    Get channel leaderboards including gifts, weekly gifts, and monthly gifts.
    """
    try:
        response = kick_api.send_request(
            f"/api/v2/channels/{channel_name}/leaderboards", method="GET"
        )

        if not response.is_success:
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail=f"Channel '{channel_name}' not found"
                )
            raise HTTPException(
                status_code=response.status_code,
                detail=response.error or "Failed to fetch leaderboards",
            )

        return {
            "gifts": response.data.get("gifts", []),
            "gifts_enabled": response.data.get("gifts_enabled", True),
            "gifts_week": response.data.get("gifts_week", []),
            "gifts_week_enabled": response.data.get("gifts_week_enabled", True),
            "gifts_month": response.data.get("gifts_month", []),
            "gifts_month_enabled": response.data.get("gifts_month_enabled", True),
        }

    except Exception as e:
        print(f"Error fetching leaderboards for channel {channel_name}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching leaderboards"
        )


@app.get(
    "/api/v2/channels/{channel_name}/me",
    response_model=Dict[str, Any],
    responses={404: {"model": ErrorResponse}},
)
async def get_channel_me(channel_name: str = Path(..., description="Channel name")):
    """
    Get current user's relationship with a channel (following status, subscription, etc.)
    """
    try:
        response = kick_api.send_request(
            f"/api/v2/channels/{channel_name}/me",
            method="GET"
        )

        if not response.is_success:
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Channel '{channel_name}' not found"
                )
            raise HTTPException(
                status_code=response.status_code,
                detail=response.error or "Failed to fetch user channel info"
            )

        return response.data

    except Exception as e:
        print(f"Error fetching user channel info for {channel_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching user channel info"
        )


@app.get(
    "/api/v2/channels/{channel_name}/polls",
    response_model=Dict[str, Any],
    responses={404: {"model": ErrorResponse}},
)
async def get_channel_polls(channel_name: str = Path(..., description="Channel name")):
    """
    Get active polls for a channel if any exist.
    """
    try:
        response = kick_api.send_request(
            f"/api/v2/channels/{channel_name}/polls",
            method="GET"
        )

        if not response.is_success:
            if response.status_code == 404:
                return {"polls": None}
            raise HTTPException(
                status_code=response.status_code,
                detail=response.error or "Failed to fetch polls"
            )

        return response.data

    except Exception as e:
        print(f"Error fetching polls for channel {channel_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching polls"
        )


@app.get(
    "/api/v2/channels/{channel_name}/info",
    response_model=Dict[str, Any],
    responses={404: {"model": ErrorResponse}},
)
async def get_channel_info(channel_name: str = Path(..., description="Channel name")):
    """
    Get detailed information about a channel including livestream status, user details, etc.
    """
    try:
        response = kick_api.send_request(
            f"/api/v2/channels/{channel_name}/info",
            method="GET"
        )

        if not response.is_success:
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Channel '{channel_name}' not found"
                )
            raise HTTPException(
                status_code=response.status_code,
                detail=response.error or "Failed to fetch channel info"
            )

        return response.data

    except Exception as e:
        print(f"Error fetching channel info for {channel_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching channel info"
        )


@app.post(
    "/api/v2/messages/send/{chatroom_id}",
    response_model=Dict[str, Any],
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def send_message(
    chatroom_id: int = Path(..., description="Chatroom ID"),
    content: str = Body(..., description="Message content"),
    type: str = Body("message", description="Message type"),
    auth: str = Depends(get_session_token),
):
    """
    Send a message to a chatroom. Requires authentication with a valid session token.
    The token should be provided in the Authorization header with format: 'Bearer your-token-here'
    """
    try:
        data = {"content": content, "type": type}
        headers = {"Authorization": auth}

        response = kick_api.send_request(
            f"/api/v2/messages/send/{chatroom_id}",
            method="POST",
            json_data=data,
            headers=headers
        )

        if not response.is_success:
            if response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or expired session token"
                )
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Chatroom '{chatroom_id}' not found"
                )
            raise HTTPException(
                status_code=response.status_code,
                detail=response.error or "Failed to send message"
            )

        return response.data

    except Exception as e:
        print(f"Error sending message to chatroom {chatroom_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while sending message"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
