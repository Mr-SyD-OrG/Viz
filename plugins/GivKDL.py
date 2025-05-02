
import os
import time
import random
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors import FloodWait, UserNotParticipant

# Replace with your API ID and Hash
API_ID = 26320112  # Replace with your actual API ID
API_HASH = "73adebcbc5ae76e8f66f3d848359ebe1"  # Replace with your actual API Hash

# Replace with your bot token
BOT_TOKEN = "8163418521:AAFbLakx4_DDCfsBfGPguoc07GjVCxfhHzM"

# Replace with your main channel ID
CHANNEL_ID = -1002189391854

# Required channels, Using both IDs and usernames
GIVEAWAY_CHANNEL_USERNAME = "KLandGiveAway"
GIVEAWAY_CHANNEL_ID = -1002189391854  # Added Giveaway Channel ID

REQUIRED_CHANNEL_USERNAME = "DumbCoconut" # CHANGED CHANNEL
REQUIRED_CHANNEL_ID = -1001938289021  # CHANGED CHANNEL

# File to store participants
PARTICIPANTS_FILE = "participants.txt"

# Time interval to check participants' membership (in seconds) - adjust as needed
MEMBERSHIP_CHECK_INTERVAL = 3600  # Check every hour

# Initialize the client
app = Client("giveaway_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# List to store the randomly picked numbers for the first round
first_round_numbers = []

# --- Helper Functions ---
async def is_user_in_channel(client, user_id, channel_id, channel_username):
    try:
        member = await client.get_chat_member(chat_id=channel_username, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except UserNotParticipant:  # Updated exception check
        return False
    except Exception as e:
        print(f"Error checking channel membership: {e}")
        return False


def add_participant(user_id):
    with open(PARTICIPANTS_FILE, "a") as f:
        f.write(str(user_id) + "\n")


def is_participant(user_id):
    if not os.path.exists(PARTICIPANTS_FILE):
        return False
    with open(PARTICIPANTS_FILE, "r") as f:
        participants = f.read().splitlines()
        return str(user_id) in participants


def get_participant_count():
    if not os.path.exists(PARTICIPANTS_FILE):
        return 0
    with open(PARTICIPANTS_FILE, "r") as f:
        participants = f.read().splitlines()
        return len(participants)


def remove_participant(user_id):
    if not os.path.exists(PARTICIPANTS_FILE):
        return

    with open(PARTICIPANTS_FILE, "r") as f:
        participants = f.read().splitlines()

    updated_participants = [p for p in participants if p != str(user_id)]

    with open(PARTICIPANTS_FILE, "w") as f:
        for p in updated_participants:
            f.write(p + "\n")


async def check_participant_membership(client):  # Added client argument
    while True:
        print("Checking participant membership...")
        try:
            with open(PARTICIPANTS_FILE, "r") as f:
                participants = f.read().splitlines()

            for user_id in participants:
                user_id = int(user_id)

                # Call the async function using await
                is_member_giveaway = await is_user_in_channel(
                    client, user_id, GIVEAWAY_CHANNEL_ID, GIVEAWAY_CHANNEL_USERNAME
                )
                is_member_required = await is_user_in_channel(
                    client, user_id, REQUIRED_CHANNEL_ID, REQUIRED_CHANNEL_USERNAME
                )

                if not is_member_giveaway or not is_member_required:
                    print(f"User {user_id} is no longer a member. Removing them.")
                    remove_participant(user_id)

        except FileNotFoundError:
            print("Participants file not found during membership check.")
        except Exception as e:
            print(f"Error during membership check: {e}")

        await asyncio.sleep(MEMBERSHIP_CHECK_INTERVAL)  # Use asyncio.sleep


# --- Command Handlers ---
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Welcome to the Giveaway Bot!")


@app.on_message(filters.command("giveaway"))
async def giveaway(client, message):
    participant_count = get_participant_count()

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="Join Giveaway", callback_data="join_giveaway"
                )
            ]
        ]
    )

    message_text = (
        "Click the button below to join the giveaway!\n\n"
        f"Current Participants: {participant_count}\n\n"
        "Requirements:\n"
        f"- Join @{GIVEAWAY_CHANNEL_USERNAME}\n" # Correct names and IDs
        f"- Join @{REQUIRED_CHANNEL_USERNAME}\n" # Correct names and IDs
    )

    try:
        await client.send_message(
            chat_id=CHANNEL_ID, text=message_text, reply_markup=keyboard
        )
    except FloodWait as e:
        print(f"FloodWait encountered: {e.value} seconds")
        await asyncio.sleep(e.value)
        await client.send_message(
            chat_id=CHANNEL_ID, text=message_text, reply_markup=keyboard
        ) #Retry
    except Exception as e:
        print(f"Error sending giveaway message: {e}")

@app.on_callback_query(filters.regex("join_giveaway"))
async def join_giveaway_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    is_member_giveaway = await is_user_in_channel(client, user_id, GIVEAWAY_CHANNEL_ID, GIVEAWAY_CHANNEL_USERNAME)
    is_member_required = await is_user_in_channel(client, user_id, REQUIRED_CHANNEL_ID, REQUIRED_CHANNEL_USERNAME)

    if not is_member_giveaway or not is_member_required: # Correct names and IDs

        await callback_query.answer(
            text=(
                "Please join the following channels and click the button again:\n"
                f"- @{GIVEAWAY_CHANNEL_USERNAME}\n"
                f"- @{REQUIRED_CHANNEL_USERNAME}\n"
            ),
            show_alert=True,
        )
    else:
        if is_participant(user_id):
            await callback_query.answer(
                "You have already participated!", show_alert=True
            )
        else:
            add_participant(user_id)
            await callback_query.answer(
                "Congratulations, you've participated!", show_alert=True
            )

@app.on_message(filters.command("random"))
async def random_numbers(client, message):
    global first_round_numbers

    try:
        number_to_pick = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.reply_text("Usage: /random <number>. Example: /random 10")
        return

    # Get total number of participants
    if os.path.exists(PARTICIPANTS_FILE):
        with open(PARTICIPANTS_FILE, "r") as f:
            participants = f.read().splitlines()
            total_participants = len(participants)
    else:
        await message.reply_text("No participants found yet.")
        return

    if number_to_pick > total_participants:
        await message.reply_text(f"You requested {number_to_pick} winners, but there are only {total_participants} participants.")
        return

    # Read participants from the file
    with open(PARTICIPANTS_FILE, "r") as f:
        participants = f.read().splitlines()

    # Convert participant IDs to integers
    participant_ids = [int(pid) for pid in participants]

    # Randomly pick numbers from participants
    first_round_numbers = random.sample(participant_ids, number_to_pick)
    first_round_numbers_str = ", ".join(map(str, first_round_numbers))

    try:
        await client.send_message(
            chat_id=CHANNEL_ID, text=f"Randomly picked winners: {first_round_numbers_str}"
        )
    except FloodWait as e:
        print(f"FloodWait encountered: {e.value} seconds")
        await asyncio.sleep(e.value)
        await client.send_message(
            chat_id=CHANNEL_ID, text=f"Randomly picked winners: {first_round_numbers_str}"
        ) #Retry
    except Exception as e:
        print(f"Error sending random winners message: {e}")

@app.on_message(filters.command("pick"))
async def pick_numbers(client, message):
    global first_round_numbers

    if not first_round_numbers:
        await message.reply_text("Please run the /random command first.")
        return

    try:
        number_to_pick = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.reply_text("Usage: /pick <number>. Example: /pick 3")
        return

    if number_to_pick > len(first_round_numbers):
        await message.reply_text(f"You can only pick a maximum of {len(first_round_numbers)} numbers.")
        return

    # Randomly pick numbers from the first_round_numbers list
    picked_numbers = random.sample(first_round_numbers, number_to_pick)
    picked_numbers_str = ", ".join(map(str, picked_numbers))

    try:
        await client.send_message(
            chat_id=CHANNEL_ID, text=f"Randomly picked from previous winners: {picked_numbers_str}"
        )
    except FloodWait as e:
        print(f"FloodWait encountered: {e.value} seconds")
        await asyncio.sleep(e.value)
        await client.send_message(
            chat_id=CHANNEL_ID, text=f"Randomly picked from previous winners: {picked_numbers_str}"
        ) #Retry
    except Exception as e:
        print(f"Error sending pick winners message: {e}")

# --- Background Task ---
async def main():
    # Create and start the membership check task
    asyncio.create_task(check_participant_membership(app))

    # Start the client
    await app.start()
    print("Bot started. Press Ctrl+C to stop.")
    await asyncio.Future()  # Keep the event loop running

if __name__ == "__main__":
    asyncio.run(main())
