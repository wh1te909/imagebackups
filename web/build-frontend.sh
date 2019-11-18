#!/bin/bash
cd /root/imagebackups/web/
rm -rf /root/imagebackups/web/node_modules/.cache
npm run build
rm -rf /var/www/imagebackups/dist/ 
mv dist /var/www/imagebackups/
systemctl restart nginx

