
deploy:
	git checkout master
	git add -A
	git commit -m "deploy blog"
	cp -r _site/ /tmp/
	git checkout gh-pages
	rm -r ./*
	cp -r /tmp/_site/* ./
	git add -A
	git commit -m "deploy blog"
	git push origin gh-pages
	git checkout master
	echo "deploy succeed"
