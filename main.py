import sys
from fastapi import FastAPI, HTTPException, Request
from google import genai
from dotenv import load_dotenv
import os
from linebot.v3.webhook import WebhookParser
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage,
    BroadcastRequest,
)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from contextlib import asynccontextmanager

load_dotenv()

channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
if channel_secret is None:
    print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

configuration = Configuration(access_token=channel_access_token)
client = genai.Client()
parser = WebhookParser(channel_secret)
line_bot_api = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    async_api_client = AsyncApiClient(configuration)
    line_bot_api = AsyncMessagingApi(async_api_client)
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/motivation")
async def root():
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            """
        คุณคือ AI ให้กำลังใจช่วยเขียนข้อความให้กำลังใจที่ทำให้ผู้อ่านรู้สึกดีขึ้น
        โดยที่คุณจะต้องให้คำตอบอย่างกระชับและไม่ต้องให้ข้อความอย่างอื่นที่ไม่เกี่ยวข้อง
        คำตอบของคุณควรจะมีความหสร้างสรรค์แปลกใหม่
        คำตอบ:
        """
        ],
    )
    return {"message": response.text}


@app.get("/")
async def test():
    return {"message": "Server is running"}


@app.post("/broadcast")
async def broadcast_message(request: Request):
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            """
        คุณคือ AI ให้กำลังใจช่วยเขียนข้อความให้กำลังใจที่ทำให้ผู้อ่านรู้สึกดีขึ้น
        โดยที่คุณจะต้องให้คำตอบอย่างกระชับและไม่ต้องให้ข้อความอย่างอื่นที่ไม่เกี่ยวข้อง
        คำตอบของคุณควรจะมีความหสร้างสรรค์แปลกใหม่
        คำตอบ:
        """
        ],
    )
    await line_bot_api.broadcast(
        BroadcastRequest(messages=[TextMessage(text=response.text)])
    )
    return {
        "message": "Broadcast sent successfully",
        "broadcasted_message": response.text,
    }


@app.post("/callback")
async def handle_callback(request: Request):
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = await request.body()
    body = body.decode()

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessageContent):
            continue
        print(
            "{} from {}: {}".format(
                event.timestamp, event.source.user_id, event.message.text
            )
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                """
        คุณคือ AI ให้กำลังใจช่วยเขียนข้อความให้กำลังใจให้ผู้อ่านรู้สึกดีขึ้น
        โดยผู้อ่านส่งมาว่า {} คุณจะต้องตอบกลับข้อความผู้อ่าน ตอบอย่างกระชับและไม่ต้องให้ข้อความอย่างอื่นที่ไม่เกี่ยวข้อง
        คำตอบของคุณควรจะมีความหมายสร้างสรรค์แปลกใหม่
        คำตอบ:
        """.format(
                    event.message.text[:200]
                ),
            ],
        )
        await line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=response.text)],
            )
        )

    return "OK"
