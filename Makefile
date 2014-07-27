
deploy:
	git checkout master
	git add -A
	git commit -m "deploy blog"
	git push
	rm -rf ~/_site
	cp -R _site ~
	git checkout gh-pages
	rm -rf ./*
	cp -R ~/_site/* ./
	git add -A
	git commit -m "deploy blog"
	git push origin gh-pages
	git checkout master
	echo "deploy succeed"
