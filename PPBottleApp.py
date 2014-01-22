from bottle import Bottle, run, template,request,TEMPLATE_PATH,static_file,HeaderDict,BaseResponse,response,redirect

import time
import urllib
import ast
import sys

import LogFeedback
import LogActivity
import requests
import os
 
from ppGuiConfig import URLToPPSearchApiSolr,GoogleAnalyticsInclusionScript,\
     LocalURLToRecordFeedback,CAS_SERVER,CAS_RETURN_SERVICE_URL,CAS_LEVEL_OF_ASSURANCE,CAS_CREATE_SESSION_IF_AUTHENTICATED,CAS_LEVEL_OF_ASSURANCE_PREDICATE

import P3Auth.auth

import cPickle as pickle
from cStringIO import StringIO

# I am duplicating this because I don't really know how t organize python 
# classes.  Probably it should be removed.
import morris_config

import pycas
import os
import cgi
import md5
import time
import urllib
import urlparse

URL_TO_MORRIS_PORTFOLIOS_API = "http://localhost:" + str(morris_config.BOTTLE_DEORATOR_PORTFOLIOS_API_PORT)

URL_TO_MORRIS_TAGS_API = "http://localhost:" + str(morris_config.BOTTLE_DEORATOR_TAGS_API_PORT)


PathToBottleWebApp = "./"
PathToExternalFiles = "../"


PathToCSSFiles=PathToExternalFiles+"css/"

app = Bottle()

PricesPaidAPIUsername=None
PricesPaidAPIPassword=None
PricesPaidAPIBasicAuthUsername=None
PricesPaidAPIBasicAuthPassword=None
P3APISALT = None


def readCredentials():
    global PricesPaidAPIUsername
    if (PricesPaidAPIUsername is None):
        global PricesPaidAPIPassword
        global PricesPaidAPIBasicAuthUsername
        global PricesPaidAPIBasicAuthPassword
        global P3APISALT
        PricesPaidAPIUsername=os.environ.get("PricesPaidAPIUsername")
        PricesPaidAPIPassword=os.environ.get("PricesPaidAPIPassword")
        PricesPaidAPIBasicAuthUsername=os.environ.get("PricesPaidAPIBasicAuthUsername")
        PricesPaidAPIBasicAuthPassword=os.environ.get("PricesPaidAPIBasicAuthPassword")
        P3APISALT=os.environ.get("P3APISALT")


# Begin Common Template Strings
FOOTER_HTML = template('Footer')
COLUMN_DROPDOWN_HTML = template('ColumnDropdown')
EXTRA_LOGIN_METHODS = template('ExtraLoginMethods')
PORTFOLIO_PANEL = template('PortfolioPanel')
MAINJS_INCLUDES = template('MainJSIncludes')
SLICKGRID_INCLUDES = template('SlickGridIncludes')
JQPLOT_INCLUDES = template('JQPlotIncludes')

# End Common Template Strings

@app.route('/theme/<path:path>')
def server_static(path):
    return static_file(path, root=PathToBottleWebApp+"theme/")

@app.route('/css/<filename>')
def server_static(filename):
    return static_file(filename, root=PathToCSSFiles)

@app.route('/js/<filename>')
def server_static(filename):
    return static_file(filename, root=PathToBottleWebApp+"js/")

@app.route('/MorrisDataDecorator/js/<filename>')
def server_static(filename):
    return static_file(filename, root="../MorrisDataDecorator/js/")
@app.route('/MorrisDataDecorator/imgs/<filename>')
def server_static(filename):
    return static_file(filename, root="../MorrisDataDecorator/imgs/")
@app.route('/MorrisDataDecorator/css/<filename>')
def server_static(filename):
    return static_file(filename, root="../MorrisDataDecorator/css/")


from bottle import template

@app.route('/')
def legalNotice():
    LogActivity.logPageTurn("nosession","LegalNotice")
    return template('LegalNotice',goog_anal_script=GoogleAnalyticsInclusionScript)

@app.route('/SearchHelp')
def searchHelp():
    LogActivity.logPageTurn("nosession","SearchHelp")
    return template('SearchHelp',goog_anal_script=GoogleAnalyticsInclusionScript)

@app.route('/Logout',method='POST')
def logoutViaPost():
    LogActivity.logPageTurn("nosession","Logout")

    acsrf = request.forms.get('antiCSRF')
    ses_id = request.forms.get('session_id')
    P3Auth.auth.del_session(ses_id)
    return template('Logout',goog_anal_script=GoogleAnalyticsInclusionScript)

@app.route('/Logout',method='GET')
def logoutViaGet():
    LogActivity.logPageTurn("nosession","Logout")

    acsrf = request.forms.get('antiCSRF')
    ses_id = request.forms.get('session_id')
    P3Auth.auth.del_session(ses_id)
    return template('Logout',goog_anal_script=GoogleAnalyticsInclusionScript)

@app.route('/Login')
def login():
    LogActivity.logPageTurn("nosession","LoginPage")
    return template('Login',message='',
                    footer_html=FOOTER_HTML,
                    extra_login_methods=EXTRA_LOGIN_METHODS,
                    goog_anal_script=GoogleAnalyticsInclusionScript)

@app.route('/LoginViaMax')
def loginViaMax():
    LogActivity.logPageTurn("nosession","MaxLoginPage")
    response.status = 303 
    domain,path = urlparse.urlparse(CAS_RETURN_SERVICE_URL)[1:3]
    secure=1
    setCookieCommand = pycas.make_pycas_cookie("gateway",domain,path,secure)
    strip = setCookieCommand[12:]
    response.set_header('Set-Cookie', strip)
    opt=""
    location = pycas.get_url_redirect_as_string(CAS_SERVER,CAS_RETURN_SERVICE_URL,opt,secure)
    response.set_header('Location',location)
    return "You will be redirected."+strip+location

@app.route('/ReturnLoginViaMax')
def returnLoginViaMax():
    LogActivity.logPageTurn("nosession","ReturnMaxLoginPage")

    ticket = request.query['ticket']
    LogActivity.logDebugInfo("MAX AUTHENTICATED ticket :"+ticket)
    status, id, cookie = pycas.check_authenticated_p(CAS_LEVEL_OF_ASSURANCE_PREDICATE,ticket,CAS_SERVER, CAS_RETURN_SERVICE_URL, lifetime=None, secure=1, protocol=2, path="/", opt="")
    maxAuthenticatedProperly = (status == pycas.CAS_OK);

    LogActivity.logDebugInfo("MAX AUTHENTICATED WITH ID:"+id)

    username = "billybob"
    if (maxAuthenticatedProperly):
        return doStartPageAuthenticated(username)
    else:
        LogActivity.logBadCredentials(username+":failed to Authenticate with Max")
        return template('Login',message='Improper Credentials.',
                    footer_html=FOOTER_HTML,
                    extra_login_methods=EXTRA_LOGIN_METHODS,
                        goog_anal_script=GoogleAnalyticsInclusionScript)


@app.route('/StartPage',method='POST')
def pptriv():
    username = request.forms.get('username')
    password = request.forms.get('password')
    # just a little throttle to slow down any denial of service attack..
    time.sleep(1.0);

    readCredentials()


    if (not P3Auth.auth.does_authenticate(username,password,P3APISALT)):
        LogActivity.logBadCredentials(username)
        return template('Login',message='Improper Credentials.',
                    footer_html=FOOTER_HTML,
                    extra_login_methods=EXTRA_LOGIN_METHODS,
                        goog_anal_script=GoogleAnalyticsInclusionScript)
    return doStartPageAuthenticated(username)

def doStartPageAuthenticated(username):
    search_string = request.forms.get('search_string')
    search_string = search_string if search_string is not None else ""
    psc_pattern = request.forms.get('psc_pattern')
    ses_id = P3Auth.auth.create_session_id()
    LogActivity.logSessionBegin(username,ses_id)
    LogActivity.logPageTurn(ses_id,"StartPage")
    return template('StartPage',search_string=search_string,\
                    acsrf=P3Auth.auth.get_acsrf(ses_id),\
                    username=username, \
                    session_id=ses_id,\
                    footer_html=FOOTER_HTML,\
                    psc_pattern=psc_pattern,goog_anal_script=GoogleAnalyticsInclusionScript)

@app.route('/StartPageReturned',method='POST')
def StartPageReturned():
    acsrf = request.forms.get('antiCSRF')
    ses_id = request.forms.get('session_id')
    if (not P3Auth.auth.is_valid_acsrf(ses_id,acsrf)):
        return template('Login',message='Improper Credentials or Timeout.',
                    extra_login_methods=EXTRA_LOGIN_METHODS,
                    footer_html=FOOTER_HTML,
                    goog_anal_script=GoogleAnalyticsInclusionScript)

    search_string = request.forms.get('search_string')
    search_string = search_string if search_string is not None else ""
    psc_pattern = request.forms.get('psc_pattern')
    ses_id = P3Auth.auth.create_session_id()
    LogActivity.logPageTurn(ses_id,"StartPageReturned")
    return template('StartPage',search_string=search_string,\
                    acsrf=P3Auth.auth.get_acsrf(ses_id),\
                    session_id=ses_id,\
                    footer_html=FOOTER_HTML,\
                    psc_pattern=psc_pattern,goog_anal_script=GoogleAnalyticsInclusionScript)

@app.route('/PricesPaid',method='GET')
def swallow(): 
    acsrf = request.query['antiCSRF']
    ses_id = request.query['session_id']
    return render_main_page(acsrf,ses_id)


@app.route('/PricesPaid',method='POST')
def pptriv():
    acsrf = request.forms.get('antiCSRF')
    ses_id = request.forms.get('session_id')
    return render_main_page(acsrf,ses_id)

def render_main_page(acsrf,ses_id):
    if (not P3Auth.auth.is_valid_acsrf(ses_id,acsrf)):
        return template('Login',message='Improper Credentials or Timeout.',
                    extra_login_methods=EXTRA_LOGIN_METHODS,
                    footer_html=FOOTER_HTML,
goog_anal_script=GoogleAnalyticsInclusionScript)
    
    P3Auth.auth.update_acsrf(ses_id)

    search_string = request.forms.get('search_string')
    search_string = search_string if search_string is not None else ""
    commodity_id = request.forms.get('commodity_id')

    LogActivity.logPageTurn(ses_id,"MainPage")
    return template('MainPage',search_string=search_string,\
                    acsrf=P3Auth.auth.get_acsrf(ses_id),\
                    session_id=ses_id,\
                    feedback_url=LocalURLToRecordFeedback,\
                    footer_html=FOOTER_HTML,\
                    portfolio_panel=PORTFOLIO_PANEL,\
                    column_dropdown=COLUMN_DROPDOWN_HTML,\
                    mainjs_includes=MAINJS_INCLUDES,\
                    slickgrid_includes=SLICKGRID_INCLUDES,\
                    jqplot_includes=JQPLOT_INCLUDES,\
                    commodity_id=commodity_id,goog_anal_script=GoogleAnalyticsInclusionScript)

@app.route('/PortfolioPage',method='POST')
def render_portfolio():
    acsrf = request.forms.get('antiCSRF')
    ses_id = request.forms.get('session_id')
    if (not P3Auth.auth.is_valid_acsrf(ses_id,acsrf)):
        return template('Login',message='Improper Credentials or Timeout.',
                    extra_login_methods=EXTRA_LOGIN_METHODS,
                    footer_html=FOOTER_HTML,
                    goog_anal_script=GoogleAnalyticsInclusionScript)

    P3Auth.auth.update_acsrf(ses_id)

    LogActivity.logPageTurn(ses_id,"Portfolio")

    portfolio = request.forms.get('portfolio')

    return template('Portfolio',acsrf=P3Auth.auth.get_acsrf(ses_id),\
                    session_id=ses_id,\
                    portfolio=portfolio,\
                    feedback_url=LocalURLToRecordFeedback,\
                    footer_html=FOOTER_HTML,\
                    portfolio_panel=PORTFOLIO_PANEL,\
                    column_dropdown=COLUMN_DROPDOWN_HTML,\
                    mainjs_includes=MAINJS_INCLUDES,\
                    slickgrid_includes=SLICKGRID_INCLUDES,\
                    jqplot_includes=JQPLOT_INCLUDES,\
                        goog_anal_script=GoogleAnalyticsInclusionScript)


@app.route('/returnPortfolio',method='POST')
def apisolr():
    acsrf = request.forms.get('antiCSRF')
    ses_id = request.forms.get('session_id')

    if (not P3Auth.auth.is_valid_acsrf(ses_id,acsrf)):
        dict = {0: {"status": "BadAuthentication"}}
        return dict;

    portfolio = request.forms.get('portfolio')

    print "portfolio = "+portfolio
    r = requests.get(URL_TO_MORRIS_PORTFOLIOS_API+"/decoration/"+portfolio)
    content = r.text
    d = ast.literal_eval(r.text)
    p3ids = d['data']

    readCredentials()

    payload = { 'username' : PricesPaidAPIUsername,\
                                'password' : PricesPaidAPIPassword,\
                                'p3ids' : pickle.dumps(p3ids)
                }

    readCredentials()

    r = requests.post(URLToPPSearchApiSolr+"/fromIds", data=payload, \
                          auth=(PricesPaidAPIBasicAuthUsername, PricesPaidAPIBasicAuthPassword), verify=False)

    LogActivity.logDebugInfo("Got Past Post to :"+URLToPPSearchApiSolr)

    content = r.text

    # This is inefficient, but I can't seem to get Bottle to
    # let me procure a correct JSON response with out using a dictionary.
    # I tried using BaseResponse.  This could be my weakness
    # with Python or confusion in Bottle.
    d = ast.literal_eval(content)
    return d

@app.route('/SimpleHTML',method='GET')
def apisolr():
    acsrf = request.query['antiCSRF']
    ses_id = request.query['session_id']

    if (not P3Auth.auth.is_valid_acsrf(ses_id,acsrf)):
        dict = {0: {"status": "BadAuthentication"}}
        return dict;

    portfolio = request.query['portfolio']

    print "portfolio = "+portfolio
    r = requests.get(URL_TO_MORRIS_PORTFOLIOS_API+"/decoration/"+portfolio)
    content = r.text
    d = ast.literal_eval(r.text)
    p3ids = d['data']

    readCredentials()

    payload = { 'username' : PricesPaidAPIUsername,\
                                'password' : PricesPaidAPIPassword,\
                                'p3ids' : pickle.dumps(p3ids)
                }

    r = requests.post(URLToPPSearchApiSolr+"/fromIds", data=payload, \
                          auth=(PricesPaidAPIBasicAuthUsername, PricesPaidAPIBasicAuthPassword), verify=False)

    LogActivity.logDebugInfo("Got Past Post to :"+URLToPPSearchApiSolr)

    content = r.text

    d = ast.literal_eval(content)
    html = ""
    for key, vdict in d.iteritems():
# Turn this into a function!
        html = html + produceHTML(vdict)
    # Actually, here we need to loop over a template, but I will try this first!
    return html

def produceHTML(valuesdict):
    html = ""

    if "productDescription" in valuesdict:
        html = html + "<h3 style= 'display:inline'>"+"Product Description: "+"</h3>"+ "<p style='display:inline'>"+ valuesdict["productDescription"]+"</p>"+"<br />"
    if "unitPrice" in valuesdict:
        html = html + "<h3 style= 'display:inline'>"+"Unit Price: "+"</h3>"+ "<p style='display:inline'>"+"$"+ valuesdict["unitPrice"]+"</p>"+"<br />"
    if "longDescription" in valuesdict:
        html = html + "<h3 style= 'display:inline'>"+"Description: "+"</h3>"+ "<p style='display:inline'>"+ valuesdict["longDescription"]+"</p>"+"<br />"
    if "unitsOrdered" in valuesdict:
        html = html + "<h3 style= 'display:inline'>"+"Units Ordered: "+"</h3>"+ "<p style='display:inline'>"+ valuesdict["unitsOrdered"]+"</p>"+"<br />"
    if "vendor" in valuesdict:
        html = html + "<h3 style= 'display:inline'>"+"Vendor: "+"</h3>"+ "<p style='display:inline'>"+ valuesdict["vendor"]+"</p>"+"<br />"
    if "orderDate" in valuesdict:
        html = html + "<h3 style= 'display:inline'>"+"Date: "+"</h3>"+ "<p style='display:inline'>"+ valuesdict["orderDate"]+"</p>"+"<br />"
    if "awardIdv" in valuesdict:
        html = html + "<h3 style= 'display:inline'>"+"Vehicle/Schedule Bought From: "+"</h3>"+ "<p style='display:inline'>"+ valuesdict["awardIdIdv"]+"</p>"+"<br />"
    if "psc" in valuesdict:
        html = html + "<h3 style= 'display:inline'>"+"PSC Code: "+"</h3>"+ "<p style='display:inline'>"+ valuesdict["psc"]+"</p>"+"<br />"
    if "contractingAgency" in valuesdict:
        html = html + "<h3 style= 'display:inline'>"+"Contracting Agency: "+"</h3>"+ "<p style='display:inline'>"+ valuesdict["contractingAgency"]+"</p>"+"<br />"     
    for k,v in valuesdict.iteritems():
        if k not in ("unitPrice","longDescription" ,"productDescription" , "unitsOrdered" , "vendor", "score", "orderDate", "p3id", 'awardIdIdv', 'psc', "contractingAgency"): 
            html = html + "<h3 style= 'display:inline'>" +k+ ":" +"</h3>"+ "<p style='display:inline'>"+str(v) + "</p>" +"<br />"+ "\n"
    html = html + "<p></p>" + "\n"
    return html

@app.route('/search',method='POST')
def apisolr():
    acsrf = request.forms.get('antiCSRF')
    ses_id = request.forms.get('session_id')

    if (not P3Auth.auth.is_valid_acsrf(ses_id,acsrf)):
        dict = {0: {"status": "BadAuthentication"}}
        return dict;

    readCredentials()

    LogActivity.logDebugInfo("Kill me: "+PricesPaidAPIBasicAuthUsername+PricesPaidAPIBasicAuthPassword)

    search_string = request.forms.get('search_string')
    psc_pattern = request.forms.get('psc_pattern')

    max_results = request.forms.get('numRows')

    LogActivity.logSearchBegun(ses_id,psc_pattern,search_string)


    payload = { 'username' : PricesPaidAPIUsername,\
                                'password' : PricesPaidAPIPassword,\
                                'search_string': search_string,\
                                'psc_pattern': psc_pattern,\
                                'numRows': max_results }

    r = requests.post(URLToPPSearchApiSolr, data=payload, \
                          auth=(PricesPaidAPIBasicAuthUsername, PricesPaidAPIBasicAuthPassword), verify=False)

    LogActivity.logDebugInfo("Got Past Post to :"+URLToPPSearchApiSolr)

    content = r.text

    # This is inefficient, but I can't seem to get Bottle to
    # let me procure a correct JSON response with out using a dictionary.
    # I tried using BaseResponse.  This could be my weakness
    # with Python or confusion in Bottle.
    d = ast.literal_eval(content)

    LogActivity.logSearchDone(ses_id,psc_pattern,search_string)
    return d

@app.route('/record_feedback',method='POST')
def feedback():
    acsrf = request.forms.get('antiCSRF')
    ses_id = request.forms.get('session_id')

    LogActivity.logDebugInfo("acsrf ses_d :"+acsrf+ses_id)
    if (not P3Auth.auth.is_valid_acsrf(ses_id,acsrf)):
        dict = {0: {"status": "BadAuthentication"}}
        return dict;

    LogActivity.logDebugInfo("authenticated !")
    LogActivity.logFeedback(ses_id)
    message = request.forms.get('message')
    name = request.forms.get('name')
    radio_list_value = request.forms.get('radio_list_value')
    LogFeedback.logFeedback(name,message,radio_list_value);
    return "true";

# This file is a directoy copy fromt he MorrisData Decorator.  It 
# out to be possible to avoid this duplication, but I don't really 
# know how to do that in Python.  I will have to spend the next day 
# in refactoring.

# BEGIN SERVER-SIDE CALLS TO MORRIS PORTFOLIO API
@app.route('/portfolio', method='GET')
def get_portfolios():
    LogActivity.logDebugInfo("Begin Get Portfolios")
    acsrf = request.query['antiCSRF']
    ses_id = request.query['session_id']
    LogActivity.logDebugInfo("Gotten on Portfolio: acsrf ses_id :"+acsrf+","+ses_id)
    if (not P3Auth.auth.is_valid_acsrf(ses_id,acsrf)):
        dict = {0: {"status": "BadAuthentication"}}
        LogActivity.logDebugInfo(" BadAuthentication :"+acsrf+","+ses_id)
        return dict;
    r = requests.get(URL_TO_MORRIS_PORTFOLIOS_API+"/decoration")
    d = ast.literal_eval(r.text)
    return d

@app.route('/portfolio/<name>', method='GET')
def get_specific_tags(name):
    acsrf = request.query['antiCSRF']
    ses_id = request.query['session_id']
    if (not P3Auth.auth.is_valid_acsrf(ses_id,acsrf)):
        dict = {0: {"status": "BadAuthentication"}}
        return dict;
    r = requests.get(URL_TO_MORRIS_PORTFOLIOS_API+"/content/"+name)
    return r.text

@app.route('/portfolio/<name>', method='POST')
def get_create_portfolio(name):
    acsrf = request.forms.get('antiCSRF')
    ses_id = request.forms.get('session_id')

    LogActivity.logDebugInfo("acsrf ses_d :"+acsrf+ses_id)
    if (not P3Auth.auth.is_valid_acsrf(ses_id,acsrf)):
        dict = {0: {"status": "BadAuthentication"}}
        return dict;
    r = requests.post(URL_TO_MORRIS_PORTFOLIOS_API+"/decoration/"+name)
    return r.text

@app.route('/portfolio_export', method='GET')
def get_export_portfolio():
    acsrf = request.query['antiCSRF']
    ses_id = request.query['session_id']
    if (not P3Auth.auth.is_valid_acsrf(ses_id,acsrf)):
        dict = {0: {"status": "BadAuthentication"}}
        return dict;
    r = requests.get(URL_TO_MORRIS_PORTFOLIOS_API+"/decoration_export")
    return r.text

@app.route('/portfolio_records', method='GET')
def get_records():
    acsrf = request.query['antiCSRF']
    ses_id = request.query['session_id']

    if (not P3Auth.auth.is_valid_acsrf(ses_id,acsrf)):
        dict = {0: {"status": "BadAuthentication"}}
        return dict;
    r = requests.get(URL_TO_MORRIS_PORTFOLIOS_API+"/decoration_records")
    return r.text

@app.route('/portfolio_records_with_cd/<columns>', method='GET')
def get_records(columns):
    acsrf = request.query['antiCSRF']
    ses_id = request.query['session_id']

    if (not P3Auth.auth.is_valid_acsrf(ses_id,acsrf)):
        dict = {0: {"status": "BadAuthentication"}}
        return dict;
    r = requests.get(URL_TO_MORRIS_PORTFOLIOS_API+"/content_records_with_client_data/"+columns)
    return r.text

@app.route('/portfolio/add_record/<portfolio>/<key>',method='POST')
def add_record_to_portfolio(key,portfolio):
    acsrf = request.forms.get('antiCSRF')
    ses_id = request.forms.get('session_id')

    LogActivity.logDebugInfo("acsrf ses_d :"+acsrf+ses_id)
    if (not P3Auth.auth.is_valid_acsrf(ses_id,acsrf)):
        dict = {0: {"status": "BadAuthentication"}}
        return dict;
    r = requests.post(URL_TO_MORRIS_PORTFOLIOS_API+"/decoration/add_record/"+portfolio+"/"+key)
    return r.text

@app.route('/portfolio/delete_decoration/<portfolio>',method='POST')
def delete_portfolio(portfolio):
    acsrf = request.forms.get('antiCSRF')
    ses_id = request.forms.get('session_id')

    LogActivity.logDebugInfo("acsrf ses_d :"+acsrf+ses_id)
    if (not P3Auth.auth.is_valid_acsrf(ses_id,acsrf)):
        dict = {0: {"status": "BadAuthentication"}}
        return dict;
    r = requests.post(URL_TO_MORRIS_PORTFOLIOS_API+"/delete_decoration/"+portfolio)
    return r.text

@app.route('/portfolio/delete_association/<portfolio>/<transaction>',method='POST')
def delete_association(portfolio,transaction):
    acsrf = request.forms.get('antiCSRF')
    ses_id = request.forms.get('session_id')

    LogActivity.logDebugInfo("acsrf ses_d :"+repr(acsrf)+' '+repr(ses_id))
    if (not P3Auth.auth.is_valid_acsrf(ses_id,acsrf)):
        dict = {0: {"status": "BadAuthentication"}}
        return dict;
    r = requests.post(URL_TO_MORRIS_PORTFOLIOS_API+"/delete_association/"+portfolio+"/"+transaction)
    return r.text

# End Portfolio work


# This is a count to keep things straight
requestNumber = 0

# map
mapRequestToReturnURL = {}


@app.route('/ReturnSessionViaMax/<requestId:int>')
def returnSessionViaMax(requestId):
    global mapRequestToReturnURL
    LogActivity.logDebugInfo("return ID:"+repr(requestId))

    LogActivity.logPageTurn("nosession","ReturnMaxLoginPage")

    ticket = request.query['ticket']
    LogActivity.logDebugInfo("MAX AUTHENTICATED ticket :"+ticket)

    amendedReturnURL = CAS_CREATE_SESSION_IF_AUTHENTICATED+"/"+repr(requestId)

    status, id, cookie = pycas.check_authenticated_p(CAS_LEVEL_OF_ASSURANCE_PREDICATE,ticket,CAS_SERVER, 
                                                     amendedReturnURL, lifetime=None, secure=1, protocol=2, path="/", opt="")
    maxAuthenticatedProperly = (status == pycas.CAS_OK);

    LogActivity.logDebugInfo("MAX AUTHENTICATED WITH ID:"+id)

    LogActivity.logDebugInfo("ReturnSessionViaMax authenticated :"+repr(maxAuthenticatedProperly))
    if (maxAuthenticatedProperly):
        sendTokensBackTo = mapRequestToReturnURL[requestId]
        response.status = 303 
        domain,path = urlparse.urlparse(CAS_RETURN_SERVICE_URL)[1:3]
        secure=1
        setCookieCommand = pycas.make_pycas_cookie("gateway",domain,path,secure)
        strip = setCookieCommand[12:]
# We will set this cookie to make it easier for the user
# to avoid multiple logins---but technically, this is not 
# what is being used and the user, who is probably using the API,
# will want to ignore this.
        response.set_header('Set-Cookie', strip)
        ses_id = P3Auth.auth.create_session_id()
        acsrf = P3Auth.auth.get_acsrf(ses_id)
        response.add_header('Location',sendTokensBackTo+"?p3session_id="+ses_id+"&p3acsrf="+acsrf)
        return "You will be redirected."+strip+sendTokensBackTo
    else:
        LogActivity.logBadCredentials("Failed to Authenticate with Max")
        return template('Login',message='Improper Credentials.',
                    footer_html=FOOTER_HTML,
                    extra_login_methods=EXTRA_LOGIN_METHODS,
                        goog_anal_script=GoogleAnalyticsInclusionScript)

@app.route('/GetTokensViaMax')
def getTokensViaMax():
    LogActivity.logPageTurn("nosession","GetTokensViaMax")
    global requestNumber
    global mapRequestToReturnURL

    sendTokensBackTo = request.query['redirectbackto']
    response.status = 303 
    domain,path = urlparse.urlparse(CAS_RETURN_SERVICE_URL)[1:3]
    secure=1
    setCookieCommand = pycas.make_pycas_cookie("gateway",domain,path,secure)
    strip = setCookieCommand[12:]
    response.set_header('Set-Cookie', strip)
    opt=""
    # There is a danger that we might have multiple requested
    # get crossed here because we are treating this "statelessly".
    # Since we need to make sure that we go back to the proper 
    # redirect, we add the request number to the URL
    amendedReturnURL = CAS_CREATE_SESSION_IF_AUTHENTICATED+"/"+repr(requestNumber)
    mapRequestToReturnURL[requestNumber] = sendTokensBackTo
    requestNumber = requestNumber + 1
    location = pycas.get_url_redirect_as_string(CAS_SERVER,amendedReturnURL,opt,secure)
    response.set_header('Location',location)
    return "You will be redirected."+strip+location

