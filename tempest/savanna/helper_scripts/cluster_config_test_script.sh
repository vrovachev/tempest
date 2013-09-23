#!/bin/bash -x

log=/tmp/log.txt

case $1 in
    NameNodeHeapSize)
        FUNC="check_nn_heap_size"
    ;;

    JobTrackerHeapSize)
        FUNC="check_jt_heap_size"
    ;;

    DataNodeHeapSize)
        FUNC="check_dn_heap_size"
    ;;

    TaskTrackerHeapSize)
        FUNC="check_tt_heap_size"
    ;;

    EnableSwift)
        FUNC="check_swift_availability"
    ;;

    dfs.replication)
        FUNC="check_dfs_replication"
    ;;

    mapred.map.tasks.speculative.execution)
        FUNC="check_mapred_map_tasks_speculative_execution"
    ;;

    mapred.child.java.opts)
        FUNC="check_mapred_child_java_opts"
    ;;
esac
shift

if [ "$1" = "-value" ]
then
    VALUE="$2"
fi
shift

check_submitted_parameter() {

    case "$1" in
        config_value)
            if [ -z "$VALUE" ]
            then
                echo "Config value is not specified" >> $log
                exit 1
            fi
        ;;
    esac
}

compare_config_values() {

check_submitted_parameter config_value

if [ "$VALUE" = "$1" ]
then
    echo -e "CHECK IS SUCCESSFUL \n\n" >> $log && exit 0
else
    echo -e "Config value while cluster creation request: $VALUE \n" >> $log
    echo -e "Actual config value on node: $1 \n" >> $log
    echo "$VALUE != $1" >> $log && exit 1
fi
}

check_heap_size() {

    heap_size=`ps aux | grep java | grep $1 | grep -o 'Xmx[0-9]\{1,10\}m' | tail -n 1 | grep -o '[0-9]\{1,100\}'`

    compare_config_values $heap_size
}

check_nn_heap_size() {

    echo -e "*******************NAME NODE HEAP SIZE******************\n" >> $log

    check_heap_size "namenode"
}

check_jt_heap_size() {

    echo -e "******************JOB TRACKER HEAP SIZE*****************\n" >> $log

    check_heap_size "jobtracker"
}

check_dn_heap_size() {

    echo -e "*******************DATA NODE HEAP SIZE******************\n" >> $log

    check_heap_size "datanode"
}

check_tt_heap_size() {

    echo -e "*****************TASK TRACKER HEAP SIZE*****************\n" >> $log

    check_heap_size "tasktracker"
}

OS_URL=""
OS_TENANT_NAME=""
OS_USERNAME=""
OS_PASSWORD=""

HADOOP_USER=""

check_return_code_after_command_execution() {

    if [ "$1" = "-exit" ]
    then
        if [ "$2" -ne 0 ]
        then
            exit 1
        fi
    fi

    if [ "$1" = "-clean_hdfs" ]
    then
        if [ "$2" -ne 0 ]
        then
            sudo su -c "hadoop dfs -rmr /swift-config-test" $HADOOP_USER && exit 1
        fi
    fi

    if [ "$1" = "-clean_hdfs_and_swift_container" ]
    then
        if [ "$2" -ne 0 ]
        then
            swift -V2.0 delete Swift-config-test
            sudo su -c "hadoop dfs -rmr /swift-config-test" $HADOOP_USER && exit 1
        fi
    fi
}

check_swift_availability() {

    echo -e "**************************SWIFT*************************\n" >> $log

    check_submitted_parameter config_value

    sudo apt-get -y --force-yes install python-pip
    sudo pip install python-swiftclient==1.2.0
    sudo pip install python-keystoneclient

    export ST_AUTH="$OS_URL"
    export ST_USER="$OS_TENANT_NAME:admin"
    export ST_KEY="$OS_PASSWORD"

    echo "Swift config test -- Enable Swift" > /tmp/swift-config-test-file.txt

    sudo su -c "hadoop dfs -mkdir /swift-config-test/" $HADOOP_USER
    check_return_code_after_command_execution -exit `echo "$?"`

    sudo su -c "hadoop dfs -copyFromLocal /tmp/swift-config-test-file.txt /swift-config-test/" $HADOOP_USER
    check_return_code_after_command_execution -clean_hdfs `echo "$?"`

    swift -V2.0 post Swift-config-test
    check_return_code_after_command_execution -clean_hdfs `echo "$?"`

    sudo su -c "hadoop distcp -D fs.swift.service.savanna.username=$OS_USERNAME -D fs.swift.service.savanna.tenant=$OS_TENANT_NAME -D fs.swift.service.savanna.password=$OS_PASSWORD /swift-config-test/swift-config-test-file.txt swift://Swift-config-test.savanna/" $HADOOP_USER
    check_return_code_after_command_execution -clean_hdfs_and_swift_container `echo "$?"`

    if [ -z `swift -V2.0 list Swift-config-test | grep -o "swift-config-test-file.txt"` ]
    then
        value="False"
    else
        value="True"
    fi

    swift -V2.0 delete Swift-config-test
    sudo su -c "hadoop dfs -rmr /swift-config-test" $HADOOP_USER

    compare_config_values $value
}

check_dfs_replication() {

    echo -e "*********************DFS.REPLICATION********************\n" >> $log

    value=`cat /etc/hadoop/hdfs-site.xml | grep -A 1 '.*dfs.replication.*' | tail -n 1 | grep -o "[0-9]\{1,10\}"`

    compare_config_values $value
}

check_mapred_map_tasks_speculative_execution() {

    echo -e "*********MAPRED.MAP.TASKS.SPECULATIVE.EXECUTION*********\n" >> $log

    value=`cat /etc/hadoop/mapred-site.xml | grep -A 1 '.*mapred.map.tasks.speculative.execution.*' | tail -n 1 | grep -o "[a-z,A-Z]\{4,5\}" | grep -v "value"`

    compare_config_values $value
}

check_mapred_child_java_opts() {

    echo -e "*****************MAPRED.CHILD.JAVA.OPTS*****************\n" >> $log

    value=`cat /etc/hadoop/mapred-site.xml | grep -A 1 '.*mapred.child.java.opts.*' | tail -n 1 | grep -o "\-Xmx[0-9]\{1,10\}m"`

    compare_config_values $value
}

$FUNC
