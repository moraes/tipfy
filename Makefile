# Convenience to run tests and coverage.
# You must have installed the App Engine SDK toolkit, version 1.4.0 or
# later, and it must be installed in /usr/local/google_appengine.
# This probably won't work on Windows.
# Borrowed from http://code.google.com/p/appengine-ndb-experiment/

FLAGS=
GAE=	/usr/local/google_appengine
GAEPATH=$(GAE):$(GAE)/lib/django_0_96:$(GAE)/lib/webob:$(GAE)/lib/yaml/lib:tests
TESTS=	`find tests -name [a-z]\*_test.py`
NONTESTS=`find tipfy -name [a-z]\*.py`
PORT=	8080
ADDRESS=localhost
PYTHON= python -Wignore
failed=0

define run_test
	PYTHONPATH=$(GAEPATH):. $(PYTHON) -m tests.$1_test $(FLAGS)
endef

test:
	for i in $(TESTS); \
    do \
      echo $$i; \
      PYTHONPATH=$(GAEPATH):. $(PYTHON) -m tests.`basename $$i .py` $(FLAGS); \
    done	

# 'app', 'auth', 'config', 'dev', 'ext_jinja2', 'ext_mako', 'gae_acl', 
# 'gae_blobstore', 'gae_db', 'gae_mail', 'gae_sharded_counter', 
# 'gae_taskqueue', 'gae_xmpp', 'i18n', 'manage', 'routing', 'secure_cookie', 
# 'sessions', 'template', 'utils'	

app_test:
	$(call run_test,app)

auth_test:
	$(call run_test,auth)

config_test:
	$(call run_test,config)

dev_test:
	$(call run_test,dev)

ext_jinja2_test:
	$(call run_test,ext_jinja2)

ext_mako_test:
	$(call run_test,ext_mako)

gae_acl_test:
	$(call run_test,gae_acl)

gae_blobstore_test:
	$(call run_test,gae_blobstore)

gae_db_test:
	$(call run_test,gae_db)

gae_mail_test:
	$(call run_test,gae_mail)

gae_sharded_counter_test:
	$(call run_test,gae_sharded_counter)

gae_taskqueue_test:
	$(call run_test,gae_taskqueue)

gae_xmpp_test:
	$(call run_test,gae_xmpp)

i18n_test:
	$(call run_test,i18n)

manage_test:
	$(call run_test,manage)

routing_test:
	$(call run_test,routing)

secure_cookie_test:
	$(call run_test,secure_cookie)

sessions_test:
	$(call run_test,sessions)

template_test:
	$(call run_test,template)

utils_test:
	$(call run_test,utils)	

c cov cove cover coverage:
	coverage erase
	for i in $(TESTS); \
	do \
	  echo $$i; \
	  PYTHONPATH=$(GAEPATH):. coverage run -p $$i; \
	done
	coverage combine
	coverage html $(NONTESTS)
	coverage report -m $(NONTESTS)
	echo "open file://`pwd`/htmlcov/index.html"

serve:
	$(GAE)/dev_appserver.py . --port $(PORT) --address $(ADDRESS)

debug:
	$(GAE)/dev_appserver.py . --port $(PORT) --address $(ADDRESS) --debug

deploy:
	appcfg.py update .

python:
	PYTHONPATH=$(GAEPATH):. $(PYTHON) -i startup.py

python_raw:
	PYTHONPATH=$(GAEPATH):. $(PYTHON)

zip:
	D=`pwd`; D=`basename $$D`; cd ..; rm $$D.zip; zip $$D.zip `hg st -c -m -a -n -X $$D/.idea $$D`

clean:
	rm -rf htmlcov
	rm -f `find . -name \*.pyc -o -name \*~ -o -name @* -o -name \*.orig`
