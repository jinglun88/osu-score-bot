import requests
import sqlite3
import prettytable

sqliteConnection = sqlite3.connect('osu.db')
osu = sqliteConnection.cursor()

def createdb():
    osu.execute("DROP TABLE IF EXISTS rankings")
    osu.execute("DROP TABLE IF EXISTS scores")
    osu.execute("CREATE TABLE rankings (username TEXT NOT NULL, id INTEGER NOT NULL PRIMARY KEY, rank INTEGER NOT NULL)")
    osu.execute("CREATE TABLE scores (id INTEGER NOT NULL, user_id INTEGER NOT NULL, beatmap_id INTEGER, accuracy FLOAT, mods TEXT, pp FLOAT, best_id INTEGER, time NUMERICAL, miss_count INTEGER, map_title TEXT, map_diff TEXT, map_stars FLOAT, FOREIGN KEY (user_id) REFERENCES rankings(id))")

def get_access_token(auth_url, client_id, client_secret):
    response = requests.post(auth_url, headers={
                                                "Accept": "application/json", 
                                                "Content-Type": "application/x-www-form-urlencoded"
                                                }, 
                                                data={
                                                "client_id": client_id, 
                                                "client_secret": client_secret, 
                                                "grant_type": "client_credentials", 
                                                "scope": "public"
                                                })
    return response.json()

url = "https://osu.ppy.sh/api/v2/"
auth_url = "https://osu.ppy.sh/oauth/token"
client_id = 36794
client_secret = "qeidWrX1X05xsjQklDpkFjHtw8rqufFqk0VQ20Ut"
token = get_access_token(auth_url, client_id, client_secret)
access_token = token["access_token"]
header_dict = {"Authorization": "Bearer "+access_token, "Accept": "application/json", "Content-Type": "application/json"}

def get_map(id):
    map = requests.get(url+"beatmaps/lookup",
                 headers=header_dict, params={"id": id}
                 )
    return map.json()

def get_ranking():
    rankings = requests.get(url+"rankings/osu/performance", headers = header_dict)
    return rankings.json()

def get_user_recents(user_id):
    recents = requests.get(url+"users/"+user_id+"/scores/recent", headers = header_dict, params = {"limit": 1000})
    return recents.json()

while True:
    choice = input("Main menu.\n1 - Make DB\n2 - Display top scores\n3 - Exit\n")
    if choice == "1":
        createdb()
        rankings = get_ranking()["ranking"] #remove cursor
        for i in range(50):
            osu.execute("INSERT INTO rankings (username, id, rank) VALUES (?, ?, ?)", [rankings[i]['user']['username'], rankings[i]['user']['id'], rankings[i]['global_rank']])
        osu.execute("SELECT id FROM rankings ORDER BY rank")
        top50 = []
        for id in osu.fetchall():
            top50.append(id[0])

        for id in top50:
            scorelist = get_user_recents(str(id))
            for score in scorelist:
                modstr = ""
                for mod in score["mods"]:
                    modstr = modstr+mod
                osu.execute("INSERT INTO scores (id, user_id, beatmap_id, accuracy, mods, pp, best_id, time, miss_count, map_title, map_diff, map_stars) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [score["id"], score["user_id"], score["beatmap"]["id"], score["accuracy"], modstr, score["pp"], score["best_id"], score["created_at"], score["statistics"]["count_miss"], score["beatmapset"]["title"], score["beatmap"]["version"], score["beatmap"]["difficulty_rating"]])
    elif choice == "2":
        score_count = int(input("How many scores? "))
        print("Top scores from the last 24 hours:")
        osu.execute("SELECT * FROM scores JOIN rankings ON scores.user_id = rankings.id ORDER BY pp DESC LIMIT ?", (str(score_count),))
        score_table= prettytable.PrettyTable(["Player", "Map", "Difficulty", "Stars", "Mods", "Accuracy", "Miss", "PP"])
        for score in osu.fetchall():
            score_table.add_row([score[12], score[9], "["+score[10]+"]", str(score[11])+"*", score[4], str(round(100*score[3], 2))+"%", str(score[8])+"x", str(score[5])+"pp"])
        print(score_table)
        print("Now that you know, do NOT check r/osugame, you will find NOTHING there. Resist the osu rot.")
    elif choice == "3":
        break