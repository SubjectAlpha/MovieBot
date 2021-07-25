import discord, re, validators, queuebot
from imdb import IMDb
from datetime import datetime

#Pretty console messages when required
def pretty_print(msg, server_id = "unknown"):
  print(f"[{get_nowf()}] {msg} [{server_id}]\n")

#return current date time formatted
def get_nowf(fmt="%d/%m/%Y %H:%M:%S"):
  now = datetime.now()
  return now.strftime(fmt)

#Return a list movie queue objects based on the server its called in
def get_movie_queue(db_ref, server_id, viewed=True):
  docs = db_ref.collection("MovieQueue").where("server_id", "==", server_id)
  if not viewed:
    docs = docs.where("viewed", "==", False).stream()
  else:
    docs = docs.stream()

  queue = queuebot.Queue()
  queue.from_collection(docs)
  return queue

def get_movie_rating(db_ref, server_id, movie_doc_id):
  movie_ratings = []
  docs = db_ref.collection("Rating").where("server_id", "==", server_id)
  docs = docs.where("movie_id", "==", movie_doc_id).stream()
  for doc in docs:
    doc = doc.to_dict()
    rating = queuebot.Rating(doc['id'], doc['server_id'], doc["movie_id"], doc['added_by'], doc['positive'])
    movie_ratings.append(rating)

  rating = 0
  for r in movie_ratings:
    if r.positive:
      rating += 1
    else:
      rating -= 1

  return {"id": movie_doc_id, "rating": rating}

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

def get_movie(db_ref, doc_id):
  movie_ref = db_ref.collection("MovieQueue").document(doc_id).get()
  movie = queuebot.Movie()
  movie.from_dict(movie_ref.to_dict())
  return movie

async def get_message_from_reference(bot_ref, msg_ref):
  server = bot_ref.get_guild(msg_ref.guild_id)
  channel = server.get_channel(msg_ref.channel_id)
  message = await channel.fetch_message(msg_ref.message_id)
  return message

async def send_queued_msg(context, message):
  try:
    await context.reply(message)
  except discord.errors.HTTPException:
    for i in range(0, len(message), 2000):
      await context.reply(message[i:i+2000])

def validate_imdb_url(url):
  if validators.url(url):
    imdb_check = re.compile("^https?:\/\/+([^:/]+\.)?imdb\.com\/title\/([-a-zA-Z0-9_\\+~#?&//=]*)")
    return imdb_check.match(url)

def check_permission(context):
  role = discord.utils.find(lambda r: r.name == 'Mods' or r.name == "Admins" or r.name == "Curator", context.guild.roles)
  if role in context.message.author.roles:
    return True
  return False
