from calendar import weekday
import country_converter as coco
import datetime
import dateutil.parser
import json
import pdfkit
from PIL import Image
import os
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
import streamlit as st
import streamlit.components.v1 as components

env = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
template = env.get_template("./templates/template.html")
badge = env.get_template("./templates/badge.html")

st.set_page_config(layout="centered", page_icon="", page_title="Badge Generator")
st.title("WCA Competition Badge Generator")

def load_image(image_file):
	img = Image.open(image_file)
	return img

def generate_events_dict(schedule):
    events = {}
    for venue in schedule['venues']:
        for room in venue['rooms']:
            for activity in room['activities']:
                events[activity['id']] = {'name': activity['name'], 'start': dateutil.parser.isoparse(activity['startTime'])}
                
                for child in activity['childActivities']:
                    events[child['id']] = {
                        'name': child['name'], 'start': dateutil.parser.isoparse(child['startTime'])}
    return dict(sorted(events.items()))


def create_personal_schedule(assignments, events):
    roles = {'competitor': 'C', 'runner' : 'R', 'scrambler': 'S'}
    
    
    person_schedule = {}
    for a in assignments:
        activity_id = a['activityId']        
        time = events[activity_id]['start']
        minute_hour = time.strftime("%H:%M")
        weekday = time.strftime("%A")
        
        assignment =roles[a['assignmentCode']]

        if weekday not in person_schedule:
            person_schedule[weekday] = {}

        person_schedule[weekday][time] = {
            'time': minute_hour,
            'event': events[activity_id]['name'],
            'role': assignment
        }
    
    sorted_schedule = dict(sorted(person_schedule.items()))
    
    for day in sorted_schedule:
        sorted_schedule[day] = dict(sorted(sorted_schedule[day].items()))

    return sorted_schedule


with st.form("template_form"):
    left, right = st.columns(2)
    logo = left.file_uploader("Upload Logo", type=['png', 'jpg', 'jpeg', 'svg'])
    wcif = right.file_uploader("Upload JSON", type=['json'])
        
    if logo is not None:
        file_details = {"filename": logo.name, "filetype": logo.type, "filesize": logo.size}
        st.write(file_details)
        st.image(load_image(logo), width=150)
        
        with open(os.path.join("static",logo.name),"wb") as f:
            f.write((logo).getbuffer())
    
    if wcif is not None:
        file_details = {"filename": wcif.name, "filetype": wcif.type, "filesize": wcif.size}	
        st.write(file_details)
        
    submit = st.form_submit_button()
    
    
if submit:
    with open('wcif.json') as f:
        data = json.load(f)

    persons = data['persons']
    schedule = data['schedule']
    
    events = generate_events_dict(schedule)

    badges = ""
    
    for p in persons:
        if (p['registration']['status'] == 'accepted') and p['registrantId'] < 10:
            person_schedule = create_personal_schedule(p['assignments'], events)

            person_badge = badge.render(
                name=p['name'],
                competitor_id=p['registrantId'],
                wca_id=p['wcaId'],
                country=coco.convert(names=p['countryIso2'], to='name_short'),
                schedule=person_schedule,
                logo = logo.name
            )

            badges += person_badge

    res = template.render(badges=badges)
    
    st.success("🎉 Your badges were generated!")

    with open("badges.html", "w") as file:
        file.write(res)
    
    with open("badges.html", "rb") as file:
        components.iframe("badges.html")