import country_converter as coco
import datetime
import dateutil.parser
import json
import pdfkit
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
import streamlit as st

env = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
template = env.get_template("./templates/template.html")
badge = env.get_template("./templates/badge.html")

st.title("")


with open('wcif.json') as f:
    data = json.load(f)

persons = data['persons']
schedule = data['schedule']


def generate_events_dict(schedule):
    events = {}
    for venue in schedule['venues']:
        for room in venue['rooms']:
            for activities in room['activities']:
                for child in activities['childActivities']:
                    events[child['id']] = {
                        'name': child['name'], 'start': dateutil.parser.isoparse(child['startTime'])}
    return events


def create_personal_schedule(assignments, events):
    person_schedule = {}
    for a in assignments:
        activity_id = a['activityId']
        time = events[activity_id]['start']
        assignment = a['assignmentCode']
        person_schedule[time] = {
            'event': events[activity_id]['name'],
            'role': assignment
        }
    sorted_schedule = dict(sorted(person_schedule.items()))
    print(sorted_schedule)

    return sorted_schedule


events = generate_events_dict(schedule)

badges = ""

for p in persons:
    if (p['registration']['status'] == 'accepted') and p['wcaUserId'] == 870:
        person_schedule = create_personal_schedule(p['assignments'], events)

        person_badge = badge.render(
            name=p['name'],
            competitor_id=p['registrantId'],
            wca_id=p['wcaId'],
            country=coco.convert(names=p['countryIso2'], to='name_short'),
            schedule=person_schedule
        )

        badges += person_badge

res = template.render(badges=badges)

with open("yourhtmlfile.html", "w") as file:
    file.write(res)
