import telebot
import sqlite3

TOKEN = "7232108334:AAGVuVTWpMP9KmL1XPROAb_VwjCFLArxtJs"
bot = telebot.TeleBot(TOKEN)

# Database Setup
conn = sqlite3.connect("anonymous_chat.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, status TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS pairs (user1 INTEGER, user2 INTEGER)")
conn.commit()

def find_pair(user_id):
    """Find an available partner for anonymous chat"""
    cursor.execute("SELECT user_id FROM users WHERE status = 'waiting' AND user_id != ?", (user_id,))
    pair = cursor.fetchone()
    
    if pair:
        pair_id = pair[0]
        cursor.execute("DELETE FROM users WHERE user_id IN (?, ?)", (user_id, pair_id))
        cursor.execute("INSERT INTO pairs (user1, user2) VALUES (?, ?)", (user_id, pair_id))
        conn.commit()
        return pair_id
    else:
        cursor.execute("INSERT INTO users (user_id, status) VALUES (?, 'waiting')", (user_id,))
        conn.commit()
        return None

def get_partner(user_id):
    """Get the partner of a user in an active chat"""
    cursor.execute("SELECT user1, user2 FROM pairs WHERE user1=? OR user2=?", (user_id, user_id))
    pair = cursor.fetchone()
    if pair:
        return pair[1] if pair[0] == user_id else pair[0]
    return None

def end_chat(user_id):
    """End an active chat"""
    cursor.execute("DELETE FROM pairs WHERE user1=? OR user2=?", (user_id, user_id))
    conn.commit()

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    bot.send_message(user_id, "Welcome to Anonymous Chat Bot! Type /next to find a chat partner.")
    
@bot.message_handler(commands=["next"])
def next_chat(message):
    user_id = message.chat.id
    partner_id = get_partner(user_id)
    
    if partner_id:
        bot.send_message(user_id, "Ending current chat...")
        bot.send_message(partner_id, "Your chat partner left. Type /next to find a new one.")
        end_chat(user_id)
    
    bot.send_message(user_id, "Searching for a new chat partner...")
    partner_id = find_pair(user_id)
    
    if partner_id:
        bot.send_message(user_id, "Connected! Start chatting.")
        bot.send_message(partner_id, "Connected! Start chatting.")

@bot.message_handler(commands=["stop"])
def stop_chat(message):
    user_id = message.chat.id
    partner_id = get_partner(user_id)

    if partner_id:
        bot.send_message(partner_id, "Your chat partner left. Type /next to find a new one.")
        end_chat(user_id)

    cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    conn.commit()

    bot.send_message(user_id, "You left the chat. Type /next to find a new partner.")

@bot.message_handler(func=lambda message: True)
def chat(message):
    user_id = message.chat.id
    partner_id = get_partner(user_id)
    
    if partner_id:
        bot.send_message(partner_id, message.text)
    else:
        bot.send_message(user_id, "You're not in a chat. Type /next to find a partner.")

bot.polling()
