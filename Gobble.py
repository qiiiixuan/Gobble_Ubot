from dotenv import load_dotenv
import logging
import os
import pandas as pd
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, constants
from telegram.ext import filters, MessageHandler, CallbackQueryHandler, ApplicationBuilder, ContextTypes, CommandHandler

load_dotenv()
API_KEY = os.getenv("TELEGRAM_BOT_TOKEN")

if not API_KEY:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Pre-assign button text
SMASH_BUTTON = "Smash"
PASS_BUTTON = "Pass"

# Build keyboards
MENU_MARKUP = InlineKeyboardMarkup([[
    InlineKeyboardButton(SMASH_BUTTON, callback_data=SMASH_BUTTON),
    InlineKeyboardButton(PASS_BUTTON, callback_data=PASS_BUTTON)
]])

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    This function would be added to the dispatcher as a handler for messages coming from the Bot API
    """

    await update.message.copy(update.message.chat_id)


async def smash(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /smash command
    """

    update.callback_query.data = SMASH_BUTTON
    await button_tap(update, context)


async def passCommand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles /pass command
    """

    update.callback_query.data = PASS_BUTTON
    await button_tap(update, context)

async def view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles /view command, returns list of saved
    """

    userId = update.message.from_user.id
    userList = pd.read_excel("Users.xlsx", sheet_name="User List")
    id = userList['UserId'].tolist().index(userId)
    indexList = str.split(userList['Saved Restaurants'][id], ", ")
    indexList = list(map(lambda x: int(x), indexList))
    await context.bot.send_message(
        update.message.from_user.id,
        text=await buildView(indexList),
        parse_mode=constants.ParseMode.HTML
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Initializes list and sends menu
    """

    userId = update.effective_chat.id
    userList = pd.read_excel("Users.xlsx", sheet_name="User List")
    if userId not in userList['UserId'].values:
        newUser = pd.DataFrame({'UserId': [userId], 'Saved Restaurants': ['']})
        userList = pd.concat([userList, newUser], ignore_index=True)
        userList.to_excel("Users.xlsx", sheet_name="User List", index=False)

    text = await buildMenu(await randomIndex(userId))

    await context.bot.send_message(
        userId,
        text=text,
        parse_mode=constants.ParseMode.HTML,
        reply_markup=MENU_MARKUP if text != "Come back tomorrow for more!" else ""
    )


async def button_tap(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processes the inline buttons on the menu
    """

    data = update.callback_query.data
    userId = update.effective_chat.id

    if data == SMASH_BUTTON:
        restaurantIndex = update.callback_query.message.text.split('\n')[0].__str__()
        userList = pd.read_excel("Users.xlsx", sheet_name="User List")
        userIndex = userList.index[userList['UserId'] == userId][0]

        savedRestaurants = userList.at[userIndex, 'Saved Restaurants']
        if savedRestaurants == '' or pd.isna(savedRestaurants):
            savedRestaurantsList = []
        else:
            savedRestaurantsList = savedRestaurants.__str__().split(', ')

        if restaurantIndex not in savedRestaurantsList:
            savedRestaurantsList.append(restaurantIndex)
            userList.at[userIndex, 'Saved Restaurants'] = ', '.join(savedRestaurantsList)
            userList.to_excel("Users.xlsx", sheet_name="User List", index=False)

    # Close the query to end the client-side loading animation
    await update.callback_query.answer()

    # Update message content with corresponding menu section
    text = await buildMenu(await randomIndex(userId))
    await update.callback_query.edit_message_text(
        text= text,
        parse_mode=constants.ParseMode.HTML,
        reply_markup=MENU_MARKUP if text != "Come back tomorrow for more!" else ""
    )

async def randomIndex(userId: int) -> int:
    """
    This function returns a random index for the restaurant list
    """

    userList = pd.read_excel("Users.xlsx", sheet_name="User List")
    userIndex = userList.index[userList['UserId'] == userId][0]
    savedRestaurants = userList.at[userIndex, 'Saved Restaurants']
    if savedRestaurants == '' or pd.isna(savedRestaurants):
        savedRestaurantsList = []
    else:
        savedRestaurantsList = savedRestaurants.__str__().split(', ')
    
    restaurantList = pd.read_excel("Restaurants.xlsx", sheet_name="Restaurant List")
    if len(savedRestaurantsList) == len(restaurantList):
        return -1
    
    randInt = random.randint(0, len(restaurantList) - 1)
    while str(randInt) in savedRestaurantsList:
        randInt = random.randint(0, len(restaurantList) - 1)
    
    return randInt


async def buildMenu(index: int) -> str:
    """
    Builds the menu as text
    """

    if index == -1:
        return "Come back tomorrow for more!"

    menu = index.__str__()
    restaurantList = pd.read_excel("Restaurants.xlsx", sheet_name="Restaurant List")
    restaurant = restaurantList.iloc[index]
    menu += f"\n\n<b>{restaurant['Name']}</b>\n<i>{restaurant['Company']}</i>\nAddress: {restaurant['Address']}\n"
    
    return menu

async def buildView(indexList: list[int]) -> str:
    """
    Builds a list of saved for view command
    """

    view = ""
    restaurantList = pd.read_excel("Restaurants.xlsx", sheet_name="Restaurant List")
    for index in indexList:
        restaurant = restaurantList.iloc[index]
        view += f"\n\n<b>{restaurant['Name']}</b>\n<i>{restaurant['Company']}</i>\nAddress: {restaurant['Address']}\n"
    
    return view


def main() -> None:
    application = ApplicationBuilder().token(API_KEY).build()

    # Register commands
    application.add_handler(CommandHandler("smash", smash))
    application.add_handler(CommandHandler("pass", passCommand))
    application.add_handler(CommandHandler("view", view))
    application.add_handler(CommandHandler("start", start))

    # Register handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_tap))

    # Echo any message that is not a command
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()