import requests
import pytz
import pprint
import datetime
import hashlib
from icalendar import Calendar, Event
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
    for dd in bs.find_all('dd'):
        try:
            dt2 = dd.previous_sibling
            dt1 = dt2.previous_sibling

            when = dt1.find('b').text.strip()
            local_tz = pytz.timezone ('America/Toronto')
            parsed_dt = datetime.datetime.strptime(when, '%A, %d %B %Y, %I:%M%p')
            local_dt = local_tz.localize(parsed_dt, is_dst=None)
            utc_dt = local_dt.astimezone (pytz.utc)

            venue = dt2.find('em').text.strip()
            where = dt1.text.split('--')[1].replace('true', '').strip()
            if '--' in dt2.text:
                dept = dt2.text.split('--')[1].strip()

            who = None
            title = None
            abstract = None
            remarks = None
            for em in dd.find_all('em'):
                if em.text == 'Speaker:':
                    who = em.next_sibling.strip()
                elif em.text == 'Title:':
                    title = em.next_sibling.next_sibling.find('em').text.strip()
                    if title[:1] == '"':
                        title = title[1:]
                    if title[-1:] == '"':
                        title = title[:-1]
                    title = title.replace('$', '')
                elif em.text == 'Abstract:':
                    # XXX TODO FIXME: This will cut off at the end of first paragraph
                    abstract = em.next_sibling.strip()
                elif em.text == 'Remarks:':
                    remarks = em.next_sibling.strip()

            event = Event()
            event['uid'] = utc_dt.strftime('%Y%m%d')+'_'+hashlib.md5(who.encode('utf-8')).hexdigest()
            event['dtstart'] = utc_dt.strftime('%Y%m%dT%H%M00Z')
            event['dtstamp'] = event['dtstart']
            event['dtend'] = (utc_dt + datetime.timedelta(hours=1)).strftime('%Y%m%dT%H%M00Z')

            event['location'] = where
            event['summary'] = title + ' - ' + dept + ' ('+ venue +')'

            event['description'] = '\n'.join(filter(None,[
                                             title,
                                             who,
                                             dept,
                                             venue,
                                             '\n',
                                             abstract,
                                             remarks]))

            yield event
        except Exception as e:
            print(dd, e)

def dump_ics(dept, name):
    cal = Calendar()
    cal.add('prodid', '-//UW-Webnotice//EN')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'UW Webnotice (%s)'%name)
    for item in get_listing(dept):
        cal.add_component(item)

    f = open('webnotice/'+dept+'.ics', 'wb')
    f.write(cal.to_ical())
    f.close()


if __name__ == '__main__':
    depts = get_depts()
    # print(depts)
    for dept in depts:
        print(depts[dept])
        dump_ics(dept, depts[dept])
    #dump_ics('all_depts', depts['all_depts'])
