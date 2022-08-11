import country_converter as coco
import dateutil.parser
import json
import pdfkit
from PIL import Image
import os
from jinja2 import Environment, select_autoescape, FileSystemLoader
import streamlit as st
import streamlit.components.v1 as components
import base64
from operator import itemgetter

env = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
template = env.get_template("./templates/template.html")
badge_template = env.get_template("./templates/badge.html")
registration_list_template = env.get_template("./templates/registration_list.html")
logo_path = "static/images/wca.png"

options = {
    'dpi': 365,
    'page-size': 'A4',
    'margin-top': '0.25in',
    'margin-right': '0.25in',
    'margin-bottom': '0.25in',
    'margin-left': '0.25in',
    'encoding': "UTF-8",
    'custom-header': [
        ('Accept-Encoding', 'gzip')
    ],
    'no-outline': None,
}


st.set_page_config(layout="wide", page_icon="🔖",
                   page_title="Badge Generator")
st.title("WCA Competition Badge Generator")


def load_image(image_file):
    img = Image.open(image_file)
    return img


def generate_events_dict(schedule):
    events = {}
    for venue in schedule['venues']:
        for room in venue['rooms']:
            for activity in room['activities']:
                events[activity['id']] = {
                    'name': activity['name'], 'start': dateutil.parser.isoparse(activity['startTime'])}

                for child in activity['childActivities']:
                    events[child['id']] = {
                        'name': child['name'], 'start': dateutil.parser.isoparse(child['startTime'])}
    return dict(sorted(events.items()))


def create_personal_schedule(assignments, events):
    roles = {'competitor': 'C', 'staff-runner': 'R',
             'staff-scrambler': 'S', 'staff-judge': 'J'}

    person_schedule = {}
    for a in assignments:
        activity_id = a['activityId']
        time = events[activity_id]['start']
        minute_hour = time.strftime("%H:%M")
        weekday = time.strftime("%A")

        assignment = roles[a['assignmentCode']]

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

def generate_badges(persons, encoded_logo):
    badges = ""
    for p in persons:
        if (p['registration']['status'] == 'accepted') and p['registrantId'] < 20:
            person_schedule = create_personal_schedule(
                p['assignments'], events)

            person_badge = badge_template.render(
                name=p['name'],
                competitor_id=p['registrantId'],
                wca_id=p['wcaId'],
                country=coco.convert(names=p['countryIso2'], to='name_short'),
                schedule=person_schedule,
                logo=encoded_logo
            )

            badges += person_badge
            
            return badges

def generate_registration_list(persons):
    registration_list_data = {}
    
    for p in persons:
        if (p['registration']['status'] == 'accepted') and p['registrantId'] < 20:
            registration_list_data[p['registrantId']] = {
                'name': p['name'],
                'wcaId': p['wcaId'],
                'birthdate': p['birthdate'] if p['birthdate'] else ''
            }
            
    registration_list = registration_list_template.render(persons = persons)

    return registration_list
            
        
  
left_upload, right_upload = st.columns(2)
logo = left_upload.file_uploader("Upload Logo", type=['png', 'jpg', 'jpeg', 'svg'])
wcif = right_upload.file_uploader("Upload JSON", type=['json'])

if logo is not None:
    file_details = {"filename": logo.name,
                        "filetype": logo.type, "filesize": logo.size}
    
    left_upload.write(file_details)
    left_upload.image(load_image(logo), width=150)

    logo_path = "static/images/" + logo.name

    with open(os.path.join(logo_path), "wb") as f:
            f.write((logo).getbuffer())

if wcif is not None:
    file_details = {"filename": wcif.name,
                        "filetype": wcif.type, "filesize": wcif.size}
    right_upload.write(file_details)

    with open(os.path.join("tmp/wcif.json"), "wb") as f:
            f.write((wcif).getbuffer())

with st.form("template_form"):
    checkbox_badges = st.checkbox('Badges', value=True)
    checkbox_registration_list = st.checkbox('Registration list')
    submit = st.form_submit_button("Generate badges!")

if submit:
    with open('tmp/wcif.json') as f:
        data = json.load(f)

    persons = sorted(data['persons'], key=itemgetter('name'))
    schedule = data['schedule']

    events = generate_events_dict(schedule)

    encoded_logo = base64.b64encode(
        open(logo_path, 'rb').read()).decode('utf-8')    

    if checkbox_badges:
        with st.spinner('Generating badges...'):
            badges = generate_badges(persons, encoded_logo)
            res = template.render(badges=badges)
            with open("static/badges.html", "w") as file:
                file.write(res)
                
        st.success("🎉 Your badges were generated!")
        pdf_badges = pdfkit.from_string(res, False, options=options)
        
        with open("static/badges.html", "r") as file:
            btn = st.download_button(
                "⬇️ Download badges as HTML",
                data=file,
                file_name="badges.html"
            )
            
        st.download_button(
            "⬇️ Download badges as PDF",
            data=pdf_badges,
            file_name="badges.pdf",
            mime="application/octet-stream",
        )
    
    
    
    
    if checkbox_registration_list:            
        registration_list = generate_registration_list(persons)
        with open("static/registration_list.html", "w") as file:
            file.write(registration_list)
        
        st.success("🎉 Your registration list was generated!")
        pdf_registration_list = pdfkit.from_string(registration_list, False, options=options)
        
        with open("static/registration_list.html", "r") as file:
            btn = st.download_button(
                "⬇️ Download registration list as HTML",
                data=file,
                file_name="registration_list.html"
            )
            
        st.download_button(
            "⬇️ Download registration list as PDF",
            data=pdf_registration_list,
            file_name="registration_list.pdf",
            mime="application/octet-stream",
        )
