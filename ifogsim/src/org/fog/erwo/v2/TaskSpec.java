package org.fog.erwo.v2;

import java.util.Map;

/**
 * Immutable task record read from an external trace. The engine never draws or alters task
 * attributes. Absolute deadline/timeout use the same binary64 addition that P01 verified
 * bit-for-bit between Python and Java.
 */
final class TaskSpec {
    final int taskId;
    final int sourceIot;
    final int accessFog;
    final String classId;
    final double arrivalS;
    final long cpuMi;
    final long inputBytes;
    final long outputBytes;
    final long workingSetBytes;
    final double deadlineRelativeS;
    final double timeoutRelativeS;
    final double deadlineAbsoluteS;
    final double timeoutAbsoluteS;

    private TaskSpec(Map<?, ?> o) {
        taskId = Json.integer(o, "task_id");
        sourceIot = Json.integer(o, "source_iot");
        accessFog = Json.integer(o, "access_fog");
        classId = (String) o.get("class_id");
        arrivalS = Json.number(o, "arrival_s");
        cpuMi = Json.longValue(o, "cpu_mi");
        inputBytes = Json.longValue(o, "input_bytes");
        outputBytes = Json.longValue(o, "output_bytes");
        workingSetBytes = Json.longValue(o, "working_set_bytes");
        deadlineRelativeS = Json.number(o, "deadline_relative_s");
        timeoutRelativeS = Json.number(o, "timeout_relative_s");
        deadlineAbsoluteS = arrivalS + deadlineRelativeS;
        timeoutAbsoluteS = arrivalS + timeoutRelativeS;
        if (taskId < 0 || sourceIot < 0 || !(arrivalS >= 0) || cpuMi < 1 || inputBytes < 1 || outputBytes < 1
                || workingSetBytes < 0 || !(deadlineRelativeS > 0) || !(timeoutRelativeS >= deadlineRelativeS)) {
            throw new IllegalArgumentException("Invalid task record: " + o);
        }
    }

    static TaskSpec fromJson(Map<?, ?> o) {
        return new TaskSpec(o);
    }

    /** Bytes of node RAM held from admission until the CPU phase ends: working set + input + output buffers. */
    long ramRequiredBytes() {
        return Math.addExact(Math.addExact(workingSetBytes, inputBytes), outputBytes);
    }
}
