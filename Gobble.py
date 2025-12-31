import os
from dotenv import load_dotenv
import logging

from telegram import Update, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import pandas as pd
import random

load_dotenv()
API_KEY = os.getenv("TELEGRAM_BOT_TOKEN")

if not API_KEY:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set")

logger = logging.getLogger(__name__)

# Pre-assign button text
SMASH_BUTTON = "Smash"
PASS_BUTTON = "Pass"

# Build keyboards
MENU_MARKUP = InlineKeyboardMarkup([[
    InlineKeyboardButton(SMASH_BUTTON, callback_data=SMASH_BUTTON),
    InlineKeyboardButton(PASS_BUTTON, callback_data=PASS_BUTTON)
]])

def echo(update: Update, context: CallbackContext) -> None:
    """
    This function would be added to the dispatcher as a handler for messages coming from the Bot API
    """

    update.message.copy(update.message.chat_id)


def smash(update: Update, context: CallbackContext) -> None:
    """
    Handles the /smash command
    """

    update.callback_query.data = SMASH_BUTTON
    button_tap(update, context)


def passCommand(update: Update, context: CallbackContext) -> None:
    """
    Handles /pass command
    """

    update.callback_query.data = PASS_BUTTON
    button_tap(update, context)

def view(update: Update, context: CallbackContext) -> None:
    """
    Handles /view command, returns list of saved
    """

    userId = update.message.from_user.id
    userList = pd.read_excel("Users.xlsx", sheet_name="User List")
    id = userList['UserId'].tolist().index(userId)
    indexList = str.split(userList['Saved Restaurants'][id], ", ")
    indexList = list(map(lambda x: int(x), indexList))
    context.bot.send_message(
        update.message.from_user.id,
        text=buildView(indexList),
        parse_mode=ParseMode.HTML
    )


def start(update: Update, context: CallbackContext) -> None:
    """
    Initializes list and sends menu
    """

    userId = update.message.from_user.id
    userList = pd.read_excel("Users.xlsx", sheet_name="User List")
    if userId not in userList['UserId'].values:
        newUser = pd.DataFrame({'UserId': [userId], 'Saved Restaurants': ['']})
        userList = pd.concat([userList, newUser], ignore_index=True)
        userList.to_excel("Users.xlsx", sheet_name="User List", index=False)

    text = buildMenu(randomIndex(userId))

    context.bot.send_message(
        userId,
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=MENU_MARKUP if text != "Come back tomorrow for more!" else ""
    )


def button_tap(update: Update, context: CallbackContext) -> None:
    """
    Processes the inline buttons on the menu
    """

    data = update.callback_query.data
    userId = update.callback_query.from_user.id

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
    update.callback_query.answer()

    # Update message content with corresponding menu section
    text = buildMenu(randomIndex(userId))
    update.callback_query.message.edit_text(
        text= text,
        parse_mode=ParseMode.HTML,
        reply_markup=MENU_MARKUP if text != "Come back tomorrow for more!" else ""
    )

def randomIndex(userId: int) -> int:
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


def buildMenu(index: int) -> str:
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

def buildView(indexList: list[int]) -> str:
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
    updater = Updater(API_KEY)

    # Get the dispatcher to register handlers
    # Then, we register each handler and the conditions the update must meet to trigger it
    dispatcher = updater.dispatcher

    # Register commands
    dispatcher.add_handler(CommandHandler("smash", smash))
    dispatcher.add_handler(CommandHandler("pass", passCommand))
    dispatcher.add_handler(CommandHandler("view", view))
    dispatcher.add_handler(CommandHandler("start", start))

    # Register handler for inline buttons
    dispatcher.add_handler(CallbackQueryHandler(button_tap))

    # Echo any message that is not a command
    dispatcher.add_handler(MessageHandler(~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()