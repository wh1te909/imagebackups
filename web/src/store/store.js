import Vue from "vue";
import Vuex from "vuex";
import axios from "axios";
import { Notify } from "quasar";

Vue.use(Vuex);

export const store = new Vuex.Store({
  state: {
    username: localStorage.getItem("user_name") || null,
    token: localStorage.getItem("access_token") || null,
    mountChoices: {},
    wipeInProgress: false,
    serverInfo: {},
    toggleDiskCheckModal: false,
    toggleVirusScanModal: false,
    diskChecks: [],
    virusScans: [],
    diskClones: []
  },
  getters: {
    loggedIn(state) {
      return state.token !== null;
    }
  },
  mutations: {
    SET_DISK_CLONES(state, info) {
      state.diskClones = info;
    },
    SET_VIRUS_SCANS(state, info) {
      state.virusScans = info;
    },
    SET_DISK_CHECKS(state, info) {
      state.diskChecks = info;
    },
    TOGGLE_DISKCHECK_MODAL(state, action) {
      state.toggleDiskCheckModal = action;
    },
    TOGGLE_VIRUSSCAN_MODAL(state, action) {
      state.toggleVirusScanModal = action;
    },
    SET_SERVER_INFO(state, info) {
      state.serverInfo = info;
    },
    SET_WIPE_STATUS(state, status) {
      state.wipeInProgress = status;
    },
    SET_MOUNT_CHOICES(state, choices) {
      state.mountChoices = choices;
    },
    retrieveToken(state, { token, username }) {
      state.token = token;
      state.username = username;
    },
    destroyCommit(state) {
      state.token = null;
      state.username = null;
    }
  },
  actions: {
    getDiskClones(context) {
      axios.get("/core/getclones/").then(r => context.commit("SET_DISK_CLONES", r.data))
    },
    getVirusScans(context) {
      axios.get("/core/getvirusscans/").then(r => context.commit("SET_VIRUS_SCANS", r.data))
    },
    getDiskChecks(context) {
      axios.get("/core/getdiskchecks/").then(r => context.commit("SET_DISK_CHECKS", r.data))
    },
    checkWipe(context) {
      axios.get("/core/getbgtask/").then(r => {
        if (r.data === 'yes') {
          context.commit("SET_WIPE_STATUS", true)
        } else if (r.data === 'no') {
          context.commit("SET_WIPE_STATUS", false)
        } else {
          context.commit("SET_WIPE_STATUS", false)
        }
      });
    },
    serverInfo(context) {
      axios.get("/core/serverinfo/").then(r => context.commit("SET_SERVER_INFO", r.data))
    },
    retrieveToken(context, credentials) {
      return new Promise((resolve, reject) => {
        axios
          .post("/login/", credentials)
          .then(response => {
            const token = response.data.token;
            const username = credentials.username;
            localStorage.setItem("access_token", token);
            localStorage.setItem("user_name", username);
            context.commit("retrieveToken", { token, username });
            resolve(response);
          })
          .catch(error => {
            Notify.create({
              color: "red",
              position: "top",
              timeout: 1000,
              textColor: "white",
              icon: "fas fa-times-circle",
              message: "Invalid credentials"
            });
            reject(error);
          });
      });
    },
    destroyToken(context) {
      if (context.getters.loggedIn) {
        return new Promise((resolve, reject) => {
          axios
            .post("/logout/")
            .then(response => {
              localStorage.removeItem("access_token");
              localStorage.removeItem("user_name");
              context.commit("destroyCommit");
              resolve(response);
            })
            .catch(error => {
              localStorage.removeItem("access_token");
              localStorage.removeItem("user_name");
              context.commit("destroyCommit");
              reject(error);
            });
        });
      }
    }
  }
});