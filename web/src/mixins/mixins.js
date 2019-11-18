import { Notify } from "quasar";

export default {
  methods: {
    notifySuccess(msg) {
      Notify.create({
        color: "green",
        icon: "fas fa-check-circle",
        message: msg
      });
    },
    notifyError(msg) {
      Notify.create({
        color: "red",
        icon: "fas fa-times-circle",
        message: msg
      });
    }
  }
};