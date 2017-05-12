import requests
import pytz
import pprint
import datetime
import hashlib
from bs4 import BeautifulSoup

wnotice = 'https://www.math.uwaterloo.ca/~wnotice/notice_prgms/wreg'
emailfrom = 'wnotice@math.uwaterloo.ca'

def get_depts():
    bs = BeautifulSoup(requests.get(wnotice+'/view_notice.pl').text, 'html5lib')
    depts = {d.attrs['value']:d.next_sibling.strip() for d in bs.find_all("input", attrs={'name':'dept'})}
    depts['all_depts'] = 'All Departments'
    return depts

def get_listing(dept):
    bs = BeautifulSoup(requests.get(wnotice+'/list_notices_p.pl?dept='+dept+'&time_frame=year').text, 'html5lib')
    events = []
    for dd in bs.find_all('dd'):
        dt2 = dd.previous_sibling
        dt1 = dt2.previous_sibling

        when = dt1.find('b').text.strip()
        local_tz = pytz.timezone ('America/Toronto')
        parsed_dt = datetime.datetime.strptime(when, '%A, %d %B %Y, %I:%M%p')
        local_dt = local_tz.localize(parsed_dt, is_dst=None)
        utc_dt = local_dt.astimezone (pytz.utc)

        event = {}
        event['when'] = utc_dt.strftime('%Y%m%dT%H%M00Z')
        event['when_end'] = (utc_dt + datetime.timedelta(hours=1)).strftime('%Y%m%dT%H%M00Z')
        event['seq'] = utc_dt.strftime('%Y%m%d%H')

        event['venue'] = dt2.find('em').text.strip()
        event['where'] = dt1.text.split('--')[1].replace('true', '').strip()
        if '--' in dt2.text:
            event['dept'] = dt2.text.split('--')[1].strip()

        for em in dd.find_all('em'):
            if em.text == 'Speaker:':
                line = em.next_sibling.strip()
                if 'Department' in line:
                    event['who'] = line.rsplit(', Department')[0].strip()
                    event['affiliation'] = 'Department ' + line.rsplit('Department')[1].strip()
                else:
                    event['who'] = line.rsplit(',')[0].strip()
                    event['affiliation'] = line.rsplit(',')[1].strip()
            elif em.text == 'Title:':
                title = em.next_sibling.next_sibling.find('em').text.strip()
                if title[:1] == '"':
                    title = title[1:]
                if title[-1:] == '"':
                    title = title[:-1]
                title = title.replace('$', '')
                event['title'] = title
            elif em.text == 'Abstract:':
                # XXX TODO FIXME: This will cut off at the end of first paragraph
                event['abstract'] = em.next_sibling.strip()
            elif em.text == 'Remarks:':
                event['remarks'] = em.next_sibling.strip()

        event['uid'] = utc_dt.strftime('%Y')+'_'+hashlib.md5((event['who']+'|'+event['title']).encode('utf-8')).hexdigest()+'.'+emailfrom
        events.append(event)
    return events

def dump_ics(dept, name):
    listing = get_listing(dept)
    fd = open('webnotice/'+dept+'.ics', 'w')
    fd.write('BEGIN:VCALENDAR\n')
    fd.write('X-WR-CALNAME:Webnotice ('+name+')\n')
    fd.write('X-WR-CALDESC:Webnotice ('+name+') at University of Waterloo\n')
    fd.write('X-PUBLISHED-TTL:PT60M\n')
    fd.write('PRODID:-//UW-Webnotice/NONSGML 0.1//EN\n')
    fd.write('VERSION:2.0\n')
    for event in listing:
        fd.write('BEGIN:VEVENT\n')
        fd.write('DTSTAMP:'+event['when']+'\n')
        fd.write('UID:'+event['uid']+'\n')
        fd.write('DTSTART:'+event['when']+'\n')
        fd.write('DTEND:'+event['when_end']+'\n')
        fd.write('SUMMARY:'+event['title']+' ('+event['venue']+')\n')
        fd.write('LOCATION:'+event['where']+'\n')
        fd.write('DESCRIPTION:'+event['title']+'\\n'+event['who']+', '+event['affiliation']+'\\n\\n')
        if 'remarks' in event:
            fd.write(event['remarks'])
            fd.write('\\n\\n')
        if 'abstract' in event:
            fd.write(event['abstract'].replace('\n', '\\n'))
    fd.write('\n')
    fd.write('END:VEVENT\n')
    fd.write('END:VCALENDAR\n')
    fd.close()

if __name__ == '__main__':
    depts = get_depts()
    print(depts)
    for dept in depts:
        dump_ics(dept, depts[dept])
