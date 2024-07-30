import os
import requests
import time
import asyncio
import io
import zipfile
import base64
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler, CallbackQueryHandler
from django.core.management.base import BaseCommand

SEARCH_TERM, NUM_IMAGES, TELEGRAM_OPTION = range(3)
TASK_STATUS_URL = 'http://103.75.199.31:8000/check_task/' 
SCRAPE_IMAGES_URL = 'http://103.75.199.31:8000/scrape_images/'
GET_SCRAPED_IMAGES_URL = 'http://103.75.199.31:8000/get_scraped_images/'
EXPORT_DB_URL = 'http://103.75.199.31:8000/export_db/'

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text('Welcome to the Image Scraper Bot! Use /scrape to start scraping images or /export_db to export the database.')

async def scrape(update: Update, context: CallbackContext):
    await update.message.reply_text('Please enter the search term for the images:')
    return SEARCH_TERM

async def get_search_term(update: Update, context: CallbackContext):
    search_term = update.message.text
    context.user_data['search_term'] = search_term
    await update.message.reply_text('How many images do you want to scrape?')
    return NUM_IMAGES

async def get_num_images(update: Update, context: CallbackContext):
    try:
        num_images = int(update.message.text)
    except ValueError:
        await update.message.reply_text('Please enter a valid number.')
        return NUM_IMAGES
    
    context.user_data['num_images'] = num_images
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data='yes')],
        [InlineKeyboardButton("No", callback_data='no')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text('Do you want to receive the images via Telegram?', reply_markup=reply_markup)
    return TELEGRAM_OPTION

async def get_telegram_option(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    telegram_option = query.data.lower()
    context.user_data['telegram_option'] = telegram_option == 'yes'
    search_term = context.user_data['search_term']
    num_images = context.user_data['num_images']

    response = requests.post(SCRAPE_IMAGES_URL, json={
        'search_term': search_term,
        'num_images': num_images
    })

    if response.status_code == 200:
        task_id = response.json().get('task_id')
        context.user_data['task_id'] = task_id
        await query.edit_message_text(f'Started scraping {num_images} images for "{search_term}". I will keep checking the status and notify you when it\'s completed.')
        
        context.application.create_task(check_task_completion(update, context, task_id, num_images))
        return ConversationHandler.END
    else:
        await query.edit_message_text('Failed to start the scraping task. Please try again.')
        return ConversationHandler.END

async def check_task_completion(update: Update, context: CallbackContext, task_id, num_images):
    while True:
        await asyncio.sleep(0.5)
        response = requests.get(f'{TASK_STATUS_URL}?task_id={task_id}')
        if response.status_code == 200:
            status = response.json().get('status')
            progress = response.json().get('progress')
            if status == 'completed':
                await update.effective_message.reply_text(f'The task for scraping images is completed.')
                await send_scraped_images(update, context, task_id)
                break
            else:
                if progress > 0:
                    await update.effective_message.reply_text(f'The task is still in progress. {progress} out of {num_images} images have been scraped. I will keep checking.')
        else:
            await update.effective_message.reply_text('Failed to check task status. Please try again later.')
            break

async def send_scraped_images(update: Update, context: CallbackContext, task_id):
    telegram_option = context.user_data.get('telegram_option', False)
    if telegram_option:
        response = requests.post(GET_SCRAPED_IMAGES_URL, json={'task_id': task_id})
        if response.status_code == 200:
            zip_buffer = io.BytesIO(response.content)
            with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                for filename in zip_file.namelist():
                    with zip_file.open(filename) as file:
                        await update.effective_message.reply_document(document=InputFile(file, filename=filename))
        else:
            error_message = f'Failed to retrieve the scraped images. Status Code: {response.status_code}, Response: {response.text}'
            await update.effective_message.reply_text(error_message)
    else:
        await update.effective_message.reply_text('The images have been scraped. (you chose not to receive them via Telegram.)')

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text('Operation cancelled.')
    return ConversationHandler.END
    
async def export_db(update: Update, context: CallbackContext):
    response = requests.post(EXPORT_DB_URL)
    if response.status_code == 200:
        file_data = io.BytesIO(response.content)
        await update.message.reply_document(document=InputFile(file_data, filename='backup.sql'))
    else:
        await update.message.reply_text(f'Failed to export the database. Status Code: {response.status_code}, Response: {response.text}')

def main():
    application = Application.builder().token('7488283693:AAFyG8P0yKswgORg-XunSWzIDPw-0Lpwf8U').build()

    scrape_handler = ConversationHandler(
        entry_points=[CommandHandler('scrape', scrape)],
        states={
            SEARCH_TERM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_search_term)],
            NUM_IMAGES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_num_images)],
            TELEGRAM_OPTION: [CallbackQueryHandler(get_telegram_option)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
  
    application.add_handler(CommandHandler('export_db', export_db))
    application.add_handler(scrape_handler)
    application.add_handler(CommandHandler('start', start))

    application.run_polling()

if __name__ == '__main__':
    main()
