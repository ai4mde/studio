$pathtojson = "/mnt/c/Users/Lucas/Downloads/runtime.json"
$copyhere = "AI4MDE/runtime/tests"

#overwrite json in windowsinput folder in repo
wsl -e bash -c "cd; cd $copyhere; cp '$pathtojson' .; cd ..; echo call generator with projectname \'latest\'; ./generator.sh latest"
#wsl -e bash -c "echo $pathtojson; cd; pwd; cd $copyhere; ls; mkdir windowsinput; cd windowsinput; pwd; cp '$pathtojson' .; cd ../..; ls; echo call generator with projectname \'latest\'& ./generator.sh latest"