(ns controller.validations
  (require [valip.core :refer [validate]]
           [valip.predicates :refer [present? integer-string? gt]]
	   [clojure.tools.logging :as log]
  ))
               
(defn in?
 "Creates a predicate that returns true if the supplied regular expression matches its argument."
 [coll]
 (fn [elm] (do
            (log/info "validating: " elm)
            (some #(= elm %) coll)
   )
  )
)

(defn positive-integer? [boundary]
 (fn [va] (do
            (and (integer-string? va)((gt boundary) va)))
   )
)

(defn valid-request? [req]
 (log/info "validating: " req)
  (validate req
    [:status present? "status must be specified"]
    [:status (in? #{"enabled" "disabled"}) "status can only have 'enabled' or 'disabled' as value"]
    [:boundary present? "boundary must be present"]
    [:boundary integer-string? "boundary must be an integer"]
    [:boundary (positive-integer? 0) "boundary must be larger than 0"]
  ))

