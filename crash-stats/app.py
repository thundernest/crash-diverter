from flask import abort, Flask, render_template, request
from flask_assets import Bundle, Environment
import helpers
import morgue_api
import settings

application = Flask(__name__, static_url_path='/static')
application.jinja_env.globals.update(settings=settings,
    **helpers.jinjafunctions, hex=hex, bool=bool)
for f in settings.FILTERS:
    application.jinja_env.filters[f] = helpers.jinjafunctions[f]

assets = Environment(application)
assets.url = application.static_url_path

@application.route("/report/<uuid>")
def view_report(uuid):
    api = morgue_api.APIHelper(uuid)
    try:
        report = api.get_results()
    except morgue_api.NotFoundError:
        abort(404)
    except ValueError:
        abort(400, 'Invalid crash id specified.')

    # TODO: Put field descriptions in here.
    # https://hg.mozilla.org/mozilla-central/file/tip/toolkit/crashreporter/CrashAnnotations.yaml
    fields_desc = {}
    report['product'] = 'Thunderbird'
    report['uuid'] = uuid
    for attr in settings.REPORT_FIELDS:
        if attr not in report:
            report[attr] = None
        fields_desc[attr] = ''
    # Rename some of these from their Backtrace names.
    report['signature'] = report['callstack']['frame'][0]
    report['address'] = report['fault.address']

    return render_template(
        'report_index.html',
        fields_desc=fields_desc, raw = {}, report=report,
        parsed_dump = {}, public_raw_keys = []
    )


@application.errorhandler(400)
def not_found(e):
    return render_template('400.html', error=e), 400


@application.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@application.errorhandler(500)
def not_found(e):
    return render_template('500.html'), 500

# Do asset bundling.
assets.register('crashstats_base', settings.SITE_CSS)
assets.register('base_js', settings.SITE_JS)

if __name__ == '__main__':
      application.run(host='0.0.0.0', port=5000)
