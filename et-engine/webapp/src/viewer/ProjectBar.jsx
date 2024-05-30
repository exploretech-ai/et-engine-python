


function ProjectBar({ project, setProject }) {

    const onOpen = () => {
        // console.log('open')
        setProject(project)
    }

    return (
        <div className="project-bar">
            {project.name}
            <button onClick={onOpen}>Open</button>
        </div>
    )
}


export default ProjectBar