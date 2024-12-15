import logging
import os
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    ConversationHandler,
    filters, 
    CallbackContext
)
from dotenv import load_dotenv
from tiktok_uploader import tiktok
from tiktok_uploader.Config import Config
from datetime import datetime
import parsedatetime

# Add this at the top with other imports
cal = parsedatetime.Calendar()

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Config
_ = Config.load("./config.txt")

# Get Telegram token from environment variable
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Define conversation states
UPLOAD_VIDEO, GET_USERNAME, GET_TITLE, GET_SCHEDULE = range(4)

# Store user data temporarily
user_data = {}

async def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        'Welcome to TikTok Uploader Bot!\n\n'
        'Commands:\n'
        '/login <name> - Login to TikTok\n'
        '/upload - Start the video upload process\n'
        '/cancel - Cancel the current operation'
    )

async def login(update: Update, context: CallbackContext) -> None:
    """Handle TikTok login."""
    try:
        if not context.args:
            await update.message.reply_text("Please provide a name for login. Usage: /login <name>")
            return

        login_name = context.args[0]
        await update.message.reply_text(f"Attempting to login with name: {login_name}")
        
        # Perform login
        tiktok.login(login_name)
        
        await update.message.reply_text(f"Successfully logged in as {login_name}")
    except Exception as e:
        await update.message.reply_text(f"Login failed: {str(e)}")
        logger.error(f"Login error: {str(e)}")

async def start_upload(update: Update, context: CallbackContext) -> int:
    """Start the upload process."""
    await update.message.reply_text(
        "Let's upload a video to TikTok!\n"
        "Please send me the video you want to upload."
    )
    return UPLOAD_VIDEO

async def handle_video(update: Update, context: CallbackContext) -> int:
    """Handle the video file."""
    try:
        video = update.message.video or update.message.document
        if not video:
            await update.message.reply_text("Please send a valid video file.")
            return UPLOAD_VIDEO

        # Download video
        await update.message.reply_text("Downloading video...")
        file = await context.bot.get_file(video.file_id)
        
        # Set the specific videos directory path
        current_directory = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(f"{current_directory}/VideosDirPath", f"{video.file_id}.mp4")
        await file.download_to_drive(file_path)

        # Store the file path in user_data
        context.user_data['file_path'] = file_path
        
        await update.message.reply_text(
            "Video received! Now, please enter the TikTok username to upload with:"
        )
        return GET_USERNAME

    except Exception as e:
        await update.message.reply_text(f"Error processing video: {str(e)}")
        return ConversationHandler.END

async def get_username(update: Update, context: CallbackContext) -> int:
    """Get the username for upload."""
    context.user_data['username'] = update.message.text
    await update.message.reply_text(
        "Great! Now, please enter the title for your video:"
    )
    return GET_TITLE

async def get_title(update: Update, context: CallbackContext) -> int:
    """Get the title for the video."""
    context.user_data['title'] = update.message.text
    await update.message.reply_text(
        "When would you like to schedule this video?\n"
        "You can use formats like:\n"
        "- MM/DD/YYYY HHpm (e.g., 12/13/2024 8pm)\n"
        "- tomorrow 3pm\n"
        "- next friday 2:30pm\n"
        "Or type 'no' for immediate upload:"
    )
    return GET_SCHEDULE

async def get_schedule(update: Update, context: CallbackContext) -> int:
    """Get the schedule time and process the upload."""
    try:
        schedule_input = update.message.text.strip().lower()
        schedule_time = 0

        if schedule_input != 'no':
            try:
                # Parse the natural language date/time
                time_struct, parse_status = cal.parse(schedule_input)
                if parse_status == 0:
                    await update.message.reply_text(
                        "Couldn't understand that date format. Please try:\n"
                        "- MM/DD/YYYY HHpm (e.g., 12/13/2024 8pm)\n"
                        "- tomorrow 3pm\n"
                        "- next friday 2:30pm\n"
                        "Or 'no' for immediate upload:"
                    )
                    return GET_SCHEDULE

                schedule_dt = datetime(*time_struct[:6])
                current_time = datetime.now()
                
                # Calculate seconds from now
                time_difference = schedule_dt - current_time
                schedule_time = int(time_difference.total_seconds())
                
                # Debug logging
                await update.message.reply_text(
                    f"Debug Info:\n"
                    f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Scheduled time: {schedule_dt.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Seconds from now: {schedule_time}"
                )

                # Check if the time is within valid range (20 minutes to 10 days)
                if schedule_time < 900:  # 15 minutes in seconds
                    await update.message.reply_text(
                        "Schedule time must be at least 20 minutes in the future.\n"
                        "Please enter a later time."
                    )
                    return GET_SCHEDULE
                    
                if schedule_time > 864000:  # 10 days in seconds
                    await update.message.reply_text(
                        "Cannot schedule video more than 10 days in advance.\n"
                        "Please enter an earlier time."
                    )
                    return GET_SCHEDULE

                # Confirm the scheduled time with user
                await update.message.reply_text(
                    f"Scheduling video for: {schedule_dt.strftime('%B %d, %Y at %I:%M %p')}\n"
                    f"({schedule_time} seconds from now)\n"
                    f"Uploading now..."
                )

            except ValueError as e:
                await update.message.reply_text(
                    "Invalid date format. Please try:\n"
                    "- MM/DD/YYYY HHpm (e.g., 12/13/2024 8pm)\n"
                    "- tomorrow 3pm\n"
                    "- next friday 2:30pm\n"
                    "Or 'no' for immediate upload"
                )
                return GET_SCHEDULE

        # Upload to TikTok
        await update.message.reply_text("Starting upload to TikTok...")
        success = tiktok.upload_video(
            context.user_data['username'],
            context.user_data['file_path'],
            context.user_data['title'],
            schedule_time=schedule_time,
            allow_comment=1,
            allow_duet=0,
            allow_stitch=0,
            visibility_type=0
        )

        # Clean up downloaded file
        if os.path.exists(context.user_data['file_path']):
            os.remove(context.user_data['file_path'])

        if success:
            if schedule_time > 0:
                schedule_dt = datetime.now() + timedelta(seconds=schedule_time)
                schedule_msg = f" (scheduled for {schedule_dt.strftime('%B %d, %Y at %I:%M %p')})"
            else:
                schedule_msg = ""
            await update.message.reply_text(f"Successfully uploaded to TikTok{schedule_msg}!")
        else:
            await update.message.reply_text("Failed to upload video to TikTok.")

    except Exception as e:
        await update.message.reply_text(f"Error during upload: {str(e)}")
        if 'file_path' in context.user_data and os.path.exists(context.user_data['file_path']):
            os.remove(context.user_data['file_path'])
    
    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel the conversation."""
    # Clean up any downloaded files
    if 'file_path' in context.user_data and os.path.exists(context.user_data['file_path']):
        os.remove(context.user_data['file_path'])
    
    # Clear user data
    context.user_data.clear()
    
    await update.message.reply_text('Upload cancelled.')
    return ConversationHandler.END

async def error_handler(update: Update, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    if update:
        await update.message.reply_text("An error occurred while processing your request.")

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('upload', start_upload)],
        states={
            UPLOAD_VIDEO: [
                MessageHandler(
                    filters.VIDEO | filters.Document.MimeType("video/mp4"), 
                    handle_video
                )
            ],
            GET_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)],
            GET_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            GET_SCHEDULE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_schedule)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("login", login))
    application.add_handler(conv_handler)

    # Add error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()