webnotice_ics
=============

Crawl webnotice and convert it to ICS format.

## Dependencies

- requests
- beautifulsoup4
- html5lib
- pytz
- icalendar

```
pip install -r requirements.txt
```

## Usage
```
python webnotice.py
```

## Customizations
In webnotice.py
 - webnotice - change this to the root of your http webnotice installation

## Output
  - creates folder webnotice/ containing all the .ics files
  - autodetects the categories/departments available and generates the appropriate ics

## Improvements

Using beatifulsoup instead of xml parser hack


## Authors

Originally developed by [Sarah Harvey](https://github.com/worldwise001/webnotice_ics)

Forked + Rewritten by [Zihao Zhang](https://github.com/zzh8829/webnotice_ics)
