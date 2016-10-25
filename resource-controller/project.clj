(defproject controller "0.1.0-SNAPSHOT"
  :description "a resource controller for CACTOS server nodes"
  :url "http://cactosfp7.eu/"
  :license {:name "Eclipse Public License"
            :url "http://www.eclipse.org/legal/epl-v10.html"}
  :dependencies [[org.clojure/clojure "1.8.0"]
                 [ring/ring-core "1.1.8"]
                 [ring/ring-json "0.4.0"]
                 [org.clojure/data.json "0.2.0"]
                 [org.clojure/tools.logging "0.3.1"]
                 [compojure "1.1.5"]
                 [valip "0.2.0"]
                ]
  :plugins [[lein-ring "0.8.3"]]

  :ring {:handler controller.core/app 
          :port 5053
          :init controller.models/checkenvb}
)

;;  :main ^:skip-aot controller.core
;;  :target-path "target/%s"
;;  :profiles {:uberjar {:aot :all}})
