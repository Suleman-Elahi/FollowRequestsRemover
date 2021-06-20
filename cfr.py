from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QDesktopWidget
import sys, time, json, csv
from datetime import datetime
import requests

class Ui(QtWidgets.QMainWindow):
    
    usernames = []
    session = None
    params = {
                '__a': '1',
                'cursor':''
             }
    
    def __init__(self):
        
        super(Ui, self).__init__()
        uic.loadUi('CFR.ui', self)
        self.cfrs.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.center()
        self.show()
        self.login_and_fetch.clicked.connect(self.buildList)
        self.delete_selected.clicked.connect(self.deleteSelectedRequests)
        self.log_out_exit.clicked.connect(self.logout)
        self.save_cfrs.clicked.connect(self.saveList)
        self.delete_all_cfr.clicked.connect(self.deleteAllRequests)
        
    def buildList(self):
        
        login = self.login(self.ig_user.text(), self.ig_pwd.text())
        login.headers.update({"x-csrftoken": login.cookies['csrftoken']})
        self.session = login
        val = 0

        while True:
            response = login.get('https://www.instagram.com/accounts/access_tool/current_follow_requests',params=self.params)
            if response.status_code == 200:
                cfr = response.json()
                for entry in cfr["data"]["data"]:
                    self.usernames.append([entry["text"]])
                if cfr["data"]["cursor"]!= None:
                    self.params['cursor'] = cfr["data"]["cursor"]
                    self.cfr_progress.setValue(val)
                    val += 4
                    time.sleep(1)
                else:
                    self.params['cursor'] = ''
                    self.cfr_progress.setValue(100)
                    break
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Error in Logging In")
                msg.setInformativeText('There\'s an error logging in')
                msg.setWindowTitle("Login Failed!")
                msg.exec_()
                break

        items = [item for x in self.usernames for item in x]
        self.cfrs.addItems(items)
        
    def login(self, username: str, password: str) -> dict:
        
        s = requests.Session()
        url = 'https://www.instagram.com/accounts/login/'
        login_url = 'https://www.instagram.com/accounts/login/ajax/'
        time = int(datetime.now().timestamp()) 
        
        s.headers.update(self.headers(""))
        response = s.get(url)
        csrf = response.cookies['csrftoken']

        payload = {
            'username': username,
            'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{time}:{password}',
            'queryParams': {},
            'optIntoOneTap': 'false'
        }
        s.headers.update({"x-csrftoken": csrf})
        login_response = s.post(login_url, data=payload)#requests.post(login_url, data=payload, headers=login_header)
        json_data = json.loads(login_response.text)

        if json_data["authenticated"]:
            return s
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error in Logging In")
        msg.setInformativeText('There\'s an error logging in')
        msg.setWindowTitle("Login Failed!")
        msg.exec_()
    
    def headers(self, xcsrf):
        req_heads = {
    'authority': 'www.instagram.com',
    'content-length': '0',
    'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
    'x-ig-www-claim': 'hmac.AR30YjH7N8MeHJGkwGSi5WOfcECA-P1DZKw3W4hHmxt1gZYx',
    'sec-ch-ua-mobile': '?1',
    'x-instagram-ajax': '1',
    'content-type': 'application/x-www-form-urlencoded',
    'accept': '*/*',
    'x-requested-with': 'XMLHttpRequest',
    'x-asbd-id': '437806',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0.1; Moto G (4)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Mobile Safari/537.36',
    'x-ig-app-id': '1217981644879628',
    'x-csrftoken': xcsrf,
    'origin': 'https://www.instagram.com',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://www.instagram.com/',
    'accept-language': 'en-US,en;q=0.9,tr;q=0.8'
                                }
        return req_heads
    
    def saveList(self):
        
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","All Files (*);;Text Files (*.txt)", options=options)
        
        with open(fileName, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(self.usernames)

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("List saved!")
        msg.setInformativeText("All the sent follow requests are saved to: "+fileName)
        msg.setWindowTitle("Current Follow Requests Saved")
        msg.exec_()
            
    def deleteSelectedRequests(self):
        
        count, pr = 0, 0
        items = self.cfrs.selectedItems()
        val = int(100/len(items))
        for i in items:
            r = self.session.get('https://www.instagram.com/'+ i.text() +'?__a=1')
            uid = r.json()["graphql"]["user"]["id"]
            response = self.session.post('https://www.instagram.com/web/friendships/'+uid+'/unfollow/')
            count += 1
            pr = pr + val
            self.cfr_progress.setValue(pr)
            self.cfrs.takeItem(self.cfrs.indexFromItem(i).row())
            time.sleep(5)
        QMessageBox.about(self, "Request Cancelled!", "Follow request cancelled for "+str(count)+" people.")
        
    def deleteAllRequests(self):
        items = [self.cfrs.item(x) for x in range(self.cfrs.count())]
        count, pr = 0, 0
        val = int(100/len(self.usernames))
        for i in items:
            r = self.session.get('https://www.instagram.com/'+ i.text() +'?__a=1')
            uid = r.json()["graphql"]["user"]["id"]
            response = self.session.post('https://www.instagram.com/web/friendships/'+uid+'/unfollow/')
            self.cfrs.takeItem(self.cfrs.indexFromItem(i).row())
            count += 1
            pr = pr + val
            self.cfr_progress.setValue(pr)
            time.sleep(5)
        QMessageBox.about(self, "Request Cancelled!", "Follow request cancelled for "+str(count)+" people.")
            
    def logout(self):
        
        post_data = {
                       'csrfmiddlewaretoken': self.session.cookies['csrftoken']
                     }
        
        logout = self.session.post('https://www.instagram.com/accounts/logout/', data=post_data)

        self.close()
        
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()
