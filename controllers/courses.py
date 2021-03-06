"""
Courses Controller
"""
import json
from flask import request

from server import app

import requests
from bs4 import BeautifulSoup

from models.setupdb import course_model, building_model, faculty_model, course_building_model


@app.route("/courses/sync", methods=["POST"])
def sync_courses():
    """
    | route: /courses/sync
    | method: POST
    | Crawles courses data from the ITU website and writes to database.
    """
    if request.method == "POST":
        base_url = "http://www.sis.itu.edu.tr/tr/ders_programlari/LSprogramlar/prg.php"
        response = requests.get(base_url)
        response.encoding = "windows-1254"
        content = response.text
        soup = BeautifulSoup(content, "lxml")

        course_codes = soup.body.find_all("select")[0].contents
        days_to_int = {
            "Pazartesi": 0,
            "Salı": 1,
            "Çarşamba": 2,
            "Perşembe": 3,
            "Cuma": 4
        }
        for opt in course_codes:
            if len(opt.string) > 0:
                # opt = course_codes[3]
                code = opt.string.strip("\n")[0:3]
                response = requests.get(base_url, params={"fb": code})
                response.encoding = "windows-1254"
                content = response.text
                soup = BeautifulSoup(content, "lxml")
                try:
                    table = soup.body.table.contents[1].contents[0].contents[5].contents[1].contents[3].contents[13].find_all(
                        "tr")
                except Exception as e:
                    continue
                key = 0
                for elem in table:
                    if key >= 2:
                        print("#######")
                        crn = elem.contents[0].string[0:5]
                        print("crn " + crn)
                        code = elem.contents[1].string
                        print("code: " + code)
                        title = elem.contents[2].string
                        print("title " + title)
                        lecturer = elem.contents[3].string
                        print("lecturer: " + lecturer)

                        try:
                            course_model.create(
                                data={"crn": int(crn), "code": code, "name": title})
                        except:
                            continue

                        anchor_tag = elem.contents[4].find("a")
                        buildings = []
                        if anchor_tag:
                            for building in anchor_tag.contents:
                                if building.string:
                                    buildings.append(building.string)
                        print("buildings: ", buildings)

                        td_day = elem.contents[5].contents
                        days = []
                        for day in td_day:
                            if day.string:
                                days.append(day.string.strip())
                        print("days: ", days)

                        td_hours = elem.contents[6].contents
                        hours = []
                        for hour in td_hours:
                            if hour.string:
                                hours.append(hour.string)
                        print("hours: ", hours)

                        i = 0
                        for d in days:
                            cday = days_to_int.get(d)
                            if cday:
                                times = hours[i].split("/")
                                start_time = times[0]
                                end_time = times[1]
                                b_result = building_model.find(
                                    query=("code='%s'" % buildings[i]))
                                if len(b_result) > 0:
                                    course_building_model.create(data={
                                        "course": int(crn),
                                        "building": b_result[0]["id"],
                                        "start_time": int(start_time),
                                        "end_time": int(end_time),
                                        "day": cday
                                    })
                            i += 1
                        # print(elem.contents[7])
                        # print(elem.contents[8].string)
                        # print(elem.contents[9].string)
                        # print(elem.contents[10].string)
                        # print(elem.contents[11].string)
                        # print(elem.contents[12])
                        # print(elem.contents[13].string)
                    key += 1

        return "done"


@app.route("/courses")
def list_courses():
    """
    | route: /courses
    | method: GET  
    | Lists courses with pagination and text query.
    """
    try:
        query = request.args["query"]
        try:
            query = int(query)
            query = "crn = %s" % query
        except ValueError:
            query = "name LIKE '{}%%' OR code LIKE '{}%%'".format(query, query)
        result = course_model.find(query=str(query))
        return json.dumps(result)
    except Exception as e:
        print(e)
        page = 0
        count = 50
        try:
            page = request.args["page"]
            count = request.args["count"]
        except:
            print("standart")
        result = course_model.find(limit=count, offset=(page * count))
        return json.dumps(result)

    
@app.route("/courses/<cid>")
def list_one_course(cid):
    """
    | route: /courses/<cid>
    | method: GET
    | param: course crn
    | Retrieves one course.
    """
    result = course_model.find_by_id(_id=cid)
    if len(result) <= 0:
        return "no course found with id %s." % cid, 404
    return json.dumps(result)


@app.route("/buildings/sync", methods=["POST"])
def sync_buildings():
    """
    | route: /buildings/sync
    | method: POST
    | Crawles all the building data from ITU website and writes to database.
    """
    if request.method == "POST":
        response = requests.get(
            "http://www.sis.itu.edu.tr/tr/sistem/bina_kodlari.html")
        response.encoding = "windows-1254"
        content = response.text
        soup = BeautifulSoup(content, "lxml")

        table = soup.body.contents[1].contents[1].contents[0].contents[5].contents[1].contents[3].contents[6].contents
        for tr in table:
            if tr.string != "\n":
                code = tr.contents[0].string
                name = tr.contents[1].string

                if name == "MEDB":
                    code = tr.contents[1].string
                    name = tr.contents[2].string

                if name == None:
                    name = tr.contents[1].contents[0].string
                result = building_model.find(query=("name='%s'" % name))
                if len(result) == 0:
                    building_model.create(
                        data={"name": name, "code": code})
    return "done"


@app.route("/buildings")
def list_buildings():
    """
    | route: /buildings
    | method: GET
    | Lists all the available buildings.
    """
    result = building_model.find()
    if result is None or len(result) <= 0:
        return "no buildings found.", 404
    return json.dumps(result)


@app.route("/buildings/<cid>")
def building_by_id(cid):
    """
    | route: /buildings/<buildingid>
    | method: GET
    | Retrieves one building with id.
    """
    result = building_model.find_by_id(_id=cid)
    if len(result) <= 0:
        return "no building found with id %s." % cid, 404
    return json.dumps(result)



@app.route("/faculties")
def list_faculties():
    """
    | route: /faculties
    | method: GET
    | Lists all the faculties.
    """
    result = faculty_model.find()
    if result is None or len(result) <= 0:
        return "no faculties found.", 404
    return json.dumps(result)


@app.route("/faculties/sync", methods=["POST"])
def sync_faculties():
    """
    | route: /faculties/sync
    | method: POST
    | Crawles all the faculties data from ITU website and writes to database.
    """
    if request.method == "POST":
        response = requests.get("http://www.sis.itu.edu.tr/tr/dersplan/")
        response.encoding = "windows-1254"
        content = response.text
        soup = BeautifulSoup(content, "lxml")

        faculty_options = soup.find_all("select")[0].contents

        for opt in faculty_options:
            if opt != "\n":
                code = opt["value"]
                name = opt.string
                if len(code) > 0:
                    result = faculty_model.find(query=("name='%s'" % name))
                    if len(result) == 0:
                        faculty_model.create(
                            data={"name": name, "code": code})
        return "done"

@app.route("/faculties/<cid>")
def faculties_by_id(cid):
    """
    | route: /buildings/<facultyid>
    | method: GET
    | Retrieves one faculty with id.
    """
    result = faculty_model.find_by_id(_id=cid)
    if len(result) <= 0:
        return "no faculty found with id %s." % cid, 404
    return json.dumps(result)
