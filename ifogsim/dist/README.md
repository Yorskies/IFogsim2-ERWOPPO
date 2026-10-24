Run the simulator from this folder with Java 27:

```powershell
java -jar ifogsim-simulator.jar 5555
```

Keep the adjacent `../jars` directory: the application manifest loads its dependencies from there, including the nested commons-math3 directory.

The JAR is generated locally and is excluded from Git. After cloning or pulling Java source changes, rebuild it before running the simulator.

Rebuild from the ifogsim directory:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

If a running server locks the existing JAR, stop that server before rebuilding, or build a separate artifact:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -JarName ifogsim-simulator-synced.jar
java -jar .\dist\ifogsim-simulator-synced.jar 5555
```

Stop the old server before starting the new server on the same port.

The entry point is `org.fog.placement.IFogSimSocketServer`. It exposes the custom TCP simulation engine used by `env_ifogsim2.py`. The socket server implements its own simulation dynamics; starting it does not run the separate CloudSim example applications.
