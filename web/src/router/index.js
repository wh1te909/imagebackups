import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '../views/Home.vue'
import Login from "@/components/Login";
import Logout from "@/components/Logout";
import NotFound from "@/components/NotFound";
import SessionExpired from "@/components/SessionExpired";


Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'home',
    component: Home,
    meta: {
      requireAuth: true
    }
  },
  {
    path: "/login",
    name: "Login",
    component: Login,
    meta: {
      requiresVisitor: true
    }
  },
  {
    path: "/logout",
    name: "Logout",
    component: Logout
  },
  {
    path: "/expired",
    name: "SessionExpired",
    component: SessionExpired,
    meta: {
      requireAuth: true
    }
  },
  { path: "*", component: NotFound }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router
