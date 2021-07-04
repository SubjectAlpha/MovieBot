import discord, os, random, validators, re
from discord.ext.commands import Bot
from imdb import IMDb
from datetime import datetime

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

#invite link https://discord.com/oauth2/authorize?client_id=858789129848225792&permissions=27712&scope=bot

bot = Bot(command_prefix='$')

cred = credentials.Certificate("fbase_auth.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

#Pretty console messages when required
def pretty_print(msg, server_id = "unknown"):
  print(f"[{get_nowf()}] {msg} [{server_id}]")

#return current date time formatted
def get_nowf(fmt="%d/%m/%Y %H:%M:%S"):
  now = datetime.now()
  return now.strftime(fmt)

#Return a list movie queue objects based on the server its called in
def get_movie_queue(server_id):
  queue = []
  docs = db.collection("MovieQueue").where("server_id", "==", server_id).stream()
  for doc in docs:
    queue.append(doc.to_dict())
  return queue

#Use IMDb library to get information on the movie requested
def get_movie_details(url):
  data = {}
  ia = IMDb()

  if validators.url(url):
    url = url.split("/")
    temp = re.compile("([a-zA-Z]+)([0-9]+)")
    res = temp.match(url[4]).groups()
    mv = ia.get_movie(res[1])
    return mv

  return data

#Add a movie based on IMDb link
@bot.command("add", help = "$add IMDb_link to add a movie to this servers queue.")
async def add_to_list(context, link):
  if validators.url(link):
    imdb_check = re.compile("^https?:\/\/+([^:/]+\.)?imdb\.com\/title\/([-a-zA-Z0-9_\\+~#?&//=]*)")
    if imdb_check.match(link):
      imdb_id = link.split("/")[4]
      details = get_movie_details(link)
      
      if not any(x['imdb_id'] == imdb_id for x in get_movie_queue(context.guild.id)):
        doc_ref = db.collection("MovieQueue").document()
        doc_ref.set({
          "id": doc_ref.id,
          "imdb_id": imdb_id,
          "server_id": context.guild.id,
          "url": link,
          "added_by": context.message.author.id,
          "date_added": get_nowf(),
          "title": details['title'],
          "rating": f"{details['rating']}/10"
        })
        await context.message.add_reaction("\N{THUMBS UP SIGN}")
      else:
        await context.reply("This movie is already on the queue")
    else:
      await context.reply("You must submit an IMDb link")
  else:
    await context.reply("You must submit an IMDb link")

#List all movies in current queue, and get info from IMDb about them.
@bot.command("list")
async def get_movie_list_message(context):
  current_queue = get_movie_queue(context.guild.id)
  queue_msg = ""
  pos = 1
  await context.message.add_reaction("\N{THUMBS UP SIGN}")
  for doc in current_queue:
    queue_msg += f"{doc['title']} - {doc['rating']} - <@{doc['added_by']}> - Position: {str(pos)}\n"
    pos += 1
  await context.reply("Current Queue:\n" + queue_msg)

#Psuedo randomly choose a movie from the saved list.
@bot.command(name="random", help="$random to randomly choose a movie from this server's queue to nominate")
async def pick_movie(context):
  current_queue = get_movie_queue(context.guild.id)
  pick = random.randint(0, len(current_queue)-1)
  movie = current_queue[pick]

  await context.reply(f"You should watch: {movie['title']} Rating: {movie['rating']}")

#Remove a movie from the list based on its current queue position.
@bot.command(name="remove", help="$remove queue_position to remove a movie from the queue")
async def remove_movie(context, movie_position):
  movie_position = int(movie_position)
  current_queue = get_movie_queue(context.guild.id)
  db.collection("MovieQueue").document(current_queue[movie_position - 1]['id']).delete()

  await context.message.add_reaction("\N{THUMBS UP SIGN}")

#Nominate a movie for watching
@bot.command(name="nominate", help="$nominate queue_position to nominate a movie of your choice.")
async def nominate_movie(context, movie_position):
  movie_position = int(movie_position)
  current_queue = get_movie_queue(context.guild.id)
  movie = current_queue[movie_position - 1]

  await context.reply(f"{movie['title']} Rating: {movie['rating']} has been nominated. Please vote with :thumbsup: or :thumbsdown:")

#Get the link for a selected movie
@bot.command(name="link", help="$link queue_position to get the link for the movie at that position in queue.")
async def get_link(context, movie_position):
  movie_position = int(movie_position)
  current_queue = get_movie_queue(context.guild.id)
  movie = current_queue[movie_position - 1]
  await context.reply(f"{movie['url']}")

#Clear channel messages
@bot.command(name="clear")
async def clear_messages(context):
  role = discord.utils.find(lambda r: r.name == 'Mods' or r.name == "Admins", context.guild.roles)
  if role in context.message.author.roles:
    await context.channel.purge(limit=120)
  else:
    await context.reply("You must be in group 'Mods' or 'Admins'")

#Status message to know when the bot is ready.
@bot.event
async def on_ready():
  pretty_print(f'We have logged in as {bot.user}')
  
bot.run(os.environ['BOT_TOKEN'])
