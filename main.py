import discord, os, random, validators, re
from discord.ext.commands import Bot
from imdb import IMDb
from datetime import datetime

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

#invite link https://discord.com/oauth2/authorize?client_id=858789129848225792&permissions=27712&scope=bot

'''
TODO:
Voting to the nomination system
-How long to leave poll open, always leave poll open?
-How to determine a winner, 2/3 of upvotes?
Add voting system in to rate users picks

Make a class for the movies to be easily imported/exported 
'''

bot = Bot(command_prefix='$')

cred = credentials.Certificate("fbase_auth.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

#Pretty console messages when required
def pretty_print(msg, server_id = "unknown"):
  print(f"[{get_nowf()}] {msg} [{server_id}]\n")

#return current date time formatted
def get_nowf(fmt="%d/%m/%Y %H:%M:%S"):
  now = datetime.now()
  return now.strftime(fmt)

#Return a list movie queue objects based on the server its called in
def get_movie_queue(server_id, viewed=False):
  queue = []
  docs = db.collection("MovieQueue").where("server_id", "==", server_id)
  if not viewed:
    docs = docs.where("viewed", "==", False).stream()
  else:
    docs = docs.stream()
  for doc in docs:
    queue.append(doc.to_dict())
  queue.sort(key=lambda x: x["date_added"])
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

async def get_message_from_reference(msg_ref):
  server = bot.get_guild(msg_ref.guild_id)
  channel = server.get_channel(msg_ref.channel_id)
  message = await channel.fetch_message(msg_ref.message_id)
  return message

#Add a movie based on IMDb link
@bot.command("add", help = "$add IMDb_link to add a movie to this servers queue.")
async def add_to_list(context, link):
  if validators.url(link):
    imdb_check = re.compile("^https?:\/\/+([^:/]+\.)?imdb\.com\/title\/([-a-zA-Z0-9_\\+~#?&//=]*)")
    if imdb_check.match(link):
      imdb_id = link.split("/")[4]
      details = get_movie_details(link)
      current_queue = get_movie_queue(context.guild.id, True)
      print(imdb_id)
      if any(x['imdb_id'] == imdb_id for x in current_queue):
        doc_ref = db.collection("MovieQueue").document()
        doc_ref.set({
          "id": doc_ref.id,
          "imdb_id": imdb_id,
          "server_id": context.guild.id,
          "url": link,
          "added_by": context.message.author.id,
          "date_added": get_nowf(),
          "title": details['title'],
          "rating": f"{details['rating']}/10",
          "viewed": False,
          "points": 0
        })
        await context.message.add_reaction("👌")
      else:
        await context.reply("This movie is already on the queue")
    else:
      await context.reply("You must submit an IMDb link")
  else:
    await context.reply("You must submit an IMDb link")

#List all movies in current queue, and get info from IMDb about them.
@bot.command("list", help="$list count to display the list up to that count default=25")
async def get_movie_list_message(context, cnt=25):
  current_queue = get_movie_queue(context.guild.id)
  queue_msg = ""
  pos = 1
  await context.message.add_reaction("👌")
  
  for doc in current_queue[:cnt]:
    queue_msg += f"{doc['title']} - {doc['rating']} - Position: {str(pos)}\n"
    pos += 1
  try:
    await context.reply("Current Queue:\n" + queue_msg)
  except discord.errors.HTTPException:
    for i in range(0, len(queue_msg), 2000):
      await context.reply(queue_msg[i:i+2000])

#Psuedo randomly choose a movie from the saved list.
@bot.command(name="random", help="$random to randomly choose a movie from this server's queue to nominate")
async def pick_random(context):
  current_queue = get_movie_queue(context.guild.id)
  pick = random.randint(0, len(current_queue)-1)
  movie = current_queue[pick]

  await context.reply(f"You should watch: {movie['title']} Rating: {movie['rating']}")

#Remove a movie from the list based on its current queue position.
@bot.command(name="remove", help="$remove queue_position to remove a movie from the queue")
async def remove_movie(context, movie_position):
  role = discord.utils.find(lambda r: r.name == 'Mods' or r.name == "Admins", context.guild.roles)
  movie_position = int(movie_position)
  current_queue = get_movie_queue(context.guild.id)
  if current_queue[movie_position - 1]["added_by"] == context.message.author.id or role in context.message.author.roles:
    db.collection("MovieQueue").document(current_queue[movie_position - 1]['id']).set({'viewed': True}, merge=True)

    await context.message.add_reaction("👌")
  else:
    await context.reply("You can only remove movies you've added")

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

@bot.command(name="top")
async def list_top_rated(context, amount=10):
  current_queue = get_movie_queue(context.guild.id, True)
  current_queue.sort(key=lambda x: x["points"])
  current_queue = current_queue[:amount]
  await context.message.add_reaction("👌")
  list_msg = ""
  for mov in current_queue:
    list_msg += f"{mov['title']} - Pts: {mov['points']} Submitter: @<{mov['added_by']}>"

  try:
    await context.reply(list_msg)
  except discord.errors.HTTPException:
    for i in range(0, len(list_msg), 2000):
      await context.reply(list_msg[i:i+2000])

#Clear channel messages
@bot.command(name="cls")
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

#Start of the voting system
@bot.event
async def on_reaction_add(reaction, user):
  if user != bot.user:
    msg = await get_message_from_reference(reaction.message.reference)
    queue_pos = int(msg.content.split()[1])
    current_queue = get_movie_queue(reaction.message.reference.guild_id)
    cur_pts = int(current_queue[queue_pos - 1]['points'])

    if reaction.emoji == "👍":
      cur_pts = cur_pts + 1
    elif reaction.emoji == "👎":
      cur_pts = cur_pts - 1
    db.collection("MovieQueue").document(current_queue[queue_pos - 1]['id']).set({'points': cur_pts}, merge=True)
  
bot.run(os.environ['BOT_TOKEN'])
