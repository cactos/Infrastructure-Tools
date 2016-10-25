(ns controller.core
  (:use compojure.core)
  (:require [compojure.route :as route]
                        [compojure.handler :as handler]
                        [ring.middleware.resource :refer [wrap-resource]]
                        [ring.middleware.params :refer [wrap-params]]
                        [ring.middleware.keyword-params :refer [wrap-keyword-params]]
                        [ring.middleware.json :refer [wrap-json-params]]
                        [clojure.data.json :as json]
                        [controller.models :as models]
                        [controller.validations :as validations]
                        [clojure.tools.logging :as log]
  ))

(require '[clojure.string :as string])

(defroutes app-routes
    (GET "/" []
         "Hello, World!")
    (GET "/vm/:id" [id]
         (try (let [result (models/vm-status-byid id)]
                (if result
                  {:status 200
                   :body (json/write-str result)
                   :headers {"Content-Type" "text/json"}
                  }
                  {:status 404 
                   :body (json/write-str 
                           {:error-message (str "virtual machine " id " does not exist.")})
                   :headers {"Content-Type" "text/json"} }
                  )
               )
              (catch RuntimeException re {:status 500 
                                          :body (json/write-str {:error-message (.getMessage re)})
                                          :headers {"Content-Type" "text/json"} })
        )
    )
  (PUT "/vm/:id" [id & params]
       (do (log/info params)
       (try 
         (let [errors (validations/valid-request? params)]
           (if errors
             {:status 400
              :body (json/write-str {:error-message errors})
              :headers {"Content-Type" "text/json"}
             }
             (let [result (models/set-vm-status id params)]
               (if result
                  {:status 204
                   ; :body (json/write-str result)
                   :headers {"Content-Type" "text/json"}
                  }
                  {:status 404
                   :body (json/write-str 
                           {:error-message (str "virtual machine " id " does not exist.")})
                   :headers {"Content-Type" "text/json"} }
               )
             )
          )
         )
         (catch RuntimeException re (do
                                     (.printStackTrace re)
                                     {:status 500
                                     :body (json/write-str {:error-message (.getMessage re)})
                                     :headers {"Content-Type" "text/json"} })
          )
       )
    )
  )
 )

  
(def app
  (-> app-routes 
;     (wrap-resource "public") 
      wrap-keyword-params
      wrap-json-params))

