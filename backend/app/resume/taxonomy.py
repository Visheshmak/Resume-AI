from dataclasses import dataclass


@dataclass(frozen=True)
class SkillDefinition:
    canonical: str
    category: str
    aliases: tuple[str, ...]


SKILL_DEFINITIONS = (
    SkillDefinition("Python", "Programming Languages", ("python",)),
    SkillDefinition("Java", "Programming Languages", ("java",)),
    SkillDefinition("JavaScript", "Programming Languages", ("javascript", "js")),
    SkillDefinition("TypeScript", "Programming Languages", ("typescript", "ts")),
    SkillDefinition("C++", "Programming Languages", ("c++", "cpp")),
    SkillDefinition("C#", "Programming Languages", ("c#", "csharp")),
    SkillDefinition("Go", "Programming Languages", ("golang",)),
    SkillDefinition("React", "Frameworks", ("react", "reactjs", "react.js")),
    SkillDefinition("Node.js", "Frameworks", ("node", "nodejs", "node.js")),
    SkillDefinition("FastAPI", "Frameworks", ("fastapi",)),
    SkillDefinition("Django", "Frameworks", ("django",)),
    SkillDefinition("Flask", "Frameworks", ("flask",)),
    SkillDefinition("Spring Boot", "Frameworks", ("spring boot",)),
    SkillDefinition("Next.js", "Frameworks", ("next.js", "nextjs")),
    SkillDefinition(".NET", "Frameworks", (".net", "dotnet")),
    SkillDefinition("Express", "Frameworks", ("express", "express.js")),
    SkillDefinition("GraphQL", "Libraries", ("graphql",)),
    SkillDefinition("Redux", "Libraries", ("redux",)),
    SkillDefinition("Pandas", "Libraries", ("pandas",)),
    SkillDefinition("NumPy", "Libraries", ("numpy",)),
    SkillDefinition("PostgreSQL", "Databases", ("postgresql", "postgres")),
    SkillDefinition("MySQL", "Databases", ("mysql",)),
    SkillDefinition("MongoDB", "Databases", ("mongodb", "mongo")),
    SkillDefinition("Redis", "Databases", ("redis",)),
    SkillDefinition("SQL", "Databases", ("sql",)),
    SkillDefinition("AWS", "Cloud", ("aws", "amazon web services")),
    SkillDefinition("Azure", "Cloud", ("azure", "microsoft azure")),
    SkillDefinition("GCP", "Cloud", ("gcp", "google cloud", "google cloud platform")),
    SkillDefinition("Docker", "DevOps", ("docker",)),
    SkillDefinition("Kubernetes", "DevOps", ("kubernetes", "k8s")),
    SkillDefinition("Terraform", "DevOps", ("terraform",)),
    SkillDefinition("CI/CD", "DevOps", ("ci/cd", "continuous integration")),
    SkillDefinition("Git", "Tools", ("git",)),
    SkillDefinition("GitHub", "Tools", ("github",)),
    SkillDefinition("Linux", "Tools", ("linux",)),
    SkillDefinition("Machine Learning", "AI/ML", ("machine learning", "ml")),
    SkillDefinition("Deep Learning", "AI/ML", ("deep learning",)),
    SkillDefinition("NLP", "AI/ML", ("nlp", "natural language processing")),
    SkillDefinition("PyTorch", "AI/ML", ("pytorch",)),
    SkillDefinition("TensorFlow", "AI/ML", ("tensorflow",)),
    SkillDefinition("Spark", "Data Engineering", ("spark", "apache spark")),
    SkillDefinition("Airflow", "Data Engineering", ("airflow", "apache airflow")),
    SkillDefinition("Communication", "Soft Skills", ("communication", "communicator")),
    SkillDefinition("Leadership", "Soft Skills", ("leadership", "led", "mentored")),
)
