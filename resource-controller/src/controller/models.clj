;
(ns controller.models
    (:refer-clojure :exclude [comment]) ;;(1)
    (:use [clojure.java.shell :only [sh]])
    (:require [clojure.string :as string])
    (:require [clojure.tools.logging :as log])
  )

(defn checkenv []
  (log/info "init called")
  )

; String name = "instance-d00001147";
; String scopeName = "machine-qemu\x2d" + name.replaceFirst("-", "x2d") + ".scope";
(defn vm-exists? [id]
  (let [out (sh "grep" id :in (:out (sh "virsh" "list" "--name")))]
    (log/info "bash script return " out)
    (if (= 0 (:exit out))
      (do ; the true case ;
       (log/info "virsh list and query successful" out)
       ;(log/info "virsh list and query successful" (string/trim (:out out)))
       ;(log/info "virsh list and query successful" out)
       (log/info "yes")
       true
      )(do ; the false case
          (if (= 1 (:exit out))
            (do
             (log/info "id not found " id " " out)
             false
            )( ; things went wrong
                throw (RuntimeException. "things went wrong. all software installed?" out)
            )
          )
      )
    )
  )
)

(defn build-systemd-scopename [vmid]
  (str "machine-qemu\\x2d" (string/replace vmid "-" "\\x2d") ".scope")
  )

(defn scope-as-map [id]
  (let [out (sh "systemctl" "show" 
                (build-systemd-scopename id)
                )]
    ; FIXME there should be a check that the call was successful
    (reduce (fn [themap pair]
              (assoc themap (nth pair 0) (nth pair 1))
              ) (hash-map) (map #(string/split % #"=") (string/split (:out out) #"\n")))
    ; FIXME we should validate that the module is activated
 )
)

(defn execute-commands [id params]
  (if (= "enabled" (get params :status))
    (do ; if case lets enable
      (log/info "executing '" "systemctl" "set-property" (build-systemd-scopename id) "CPUAccounting=true" "'")
        (let [result (sh "systemctl" "set-property" (build-systemd-scopename id) "CPUAccounting=true")]
            (if (= 0 (:exit result))
               (do ; first step successful 
                (log/info  "systemctl" "set-property" (build-systemd-scopename id)
                    (str "CPUQuota" "=" (get params :boundary) "%" ))
                (sh  "systemctl" "set-property" (build-systemd-scopename id) 
                    (str "CPUQuota" "=" (get params :boundary) "%" ) 
                )
              )
              result ; return failed result
          )
      )
    )
    (do ; else case lets disable
      (log/info "executing '" "systemctl" "set-property" (build-systemd-scopename id) "CPUAccounting=false" "'")
      (sh "systemctl" "set-property" (build-systemd-scopename id) "CPUAccounting=false")
    )
  )
)

(defn do-set-vm-status [id params]
  (let [result (execute-commands id params)]
     (if (= 0 (:exit result))
      result
      (throw (RuntimeException. (str "things went wrong. could not set properties! " 
                                (:err result) " " (:out result))))
    )
  )
)

(defn set-vm-status [id params]
 (log/info "set-vm-status " id params)
 (if (vm-exists? id)
   (do-set-vm-status id params)
   (do
     (log/info "VM does not exist " id)
     false
   )
  )
 )

(defn vm-status-byid [id]
    (log/info "vm-status-byid " id)
    (if (vm-exists? id)
      (do
        (str "VM exists " id)
        (let [abc (scope-as-map id)]
          (log/info "scope as map: " abc)
          abc
          )
      )
      (do
        (log/info "VM does not exist " id)
        false
      )
    )
;  (->
;    (let [out (sh "ls" "-l")]
;    (print out)
;      "Hello" 
;    )
;    )
)
