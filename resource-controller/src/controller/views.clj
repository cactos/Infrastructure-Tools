(ns controller.views
    (:require [hiccup.page :refer [html5 include-js include-css]]
                          [hiccup.form :refer [form-to text-field submit-button text-area]]
                          [ring.util.response :as response]
    ))

(defn index []
    (response/redirect "/projects"))

(defn vm-status [vmid]
  vmid
  )

