-- TAWOS reduzido: dados reais, sem comentarios ou historico de alteracoes.
-- Projeto 1; sprints [63, 62]; 40 tarefas.
-- Usa o banco selecionado pelo cliente MySQL; substitui as 13 tabelas do dataset.
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE;
SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO';

DROP TABLE IF EXISTS `Affected_Version`;
CREATE TABLE `Affected_Version` (
  `Issue_ID` int DEFAULT NULL,
  `Affected_Version_ID` int DEFAULT NULL,
  KEY `Affected_Version_ID` (`Affected_Version_ID`),
  KEY `F_Key` (`Issue_ID`,`Affected_Version_ID`),
  CONSTRAINT `affected_version_ibfk_1` FOREIGN KEY (`Issue_ID`) REFERENCES `Issue` (`ID`),
  CONSTRAINT `affected_version_ibfk_2` FOREIGN KEY (`Affected_Version_ID`) REFERENCES `Version` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `Change_Log`;
CREATE TABLE `Change_Log` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Field` varchar(512) DEFAULT NULL,
  `From_Value` mediumtext,
  `To_Value` mediumtext,
  `From_String` mediumtext,
  `To_String` mediumtext,
  `Change_Type` varchar(512) DEFAULT NULL,
  `Creation_Date` datetime DEFAULT NULL,
  `Author_ID` int DEFAULT NULL,
  `Issue_ID` int DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `Issue_ID` (`Issue_ID`),
  KEY `P_Key` (`ID`),
  KEY `F_Key` (`Author_ID`,`Issue_ID`),
  CONSTRAINT `change_log_ibfk_1` FOREIGN KEY (`Issue_ID`) REFERENCES `Issue` (`ID`),
  CONSTRAINT `change_log_ibfk_2` FOREIGN KEY (`Author_ID`) REFERENCES `User` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `Comment`;
CREATE TABLE `Comment` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Comment` mediumtext,
  `Comment_Text` mediumtext,
  `Comment_Code` mediumtext,
  `Creation_Date` datetime DEFAULT NULL,
  `Author_ID` int DEFAULT NULL,
  `Issue_ID` int DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `Issue_ID` (`Issue_ID`),
  KEY `P_Key` (`ID`),
  KEY `F_Key` (`Author_ID`,`Issue_ID`),
  CONSTRAINT `comment_ibfk_1` FOREIGN KEY (`Issue_ID`) REFERENCES `Issue` (`ID`),
  CONSTRAINT `comment_ibfk_2` FOREIGN KEY (`Author_ID`) REFERENCES `User` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `Component`;
CREATE TABLE `Component` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Jira_ID` int DEFAULT NULL,
  `Name` varchar(512) DEFAULT NULL,
  `Description` varchar(512) DEFAULT NULL,
  `Project_ID` int DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `P_Key` (`ID`),
  KEY `F_Key` (`Project_ID`),
  CONSTRAINT `component_ibfk_1` FOREIGN KEY (`Project_ID`) REFERENCES `Project` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `Fix_Version`;
CREATE TABLE `Fix_Version` (
  `Issue_ID` int DEFAULT NULL,
  `Fix_Version_ID` int DEFAULT NULL,
  KEY `F_Key` (`Issue_ID`,`Fix_Version_ID`),
  KEY `fix_version_ibfk_2` (`Fix_Version_ID`),
  CONSTRAINT `fix_version_ibfk_1` FOREIGN KEY (`Issue_ID`) REFERENCES `Issue` (`ID`),
  CONSTRAINT `fix_version_ibfk_2` FOREIGN KEY (`Fix_Version_ID`) REFERENCES `Version` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `Issue`;
CREATE TABLE `Issue` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Jira_ID` int DEFAULT NULL,
  `Issue_Key` varchar(512) DEFAULT NULL,
  `URL` varchar(512) DEFAULT NULL,
  `Title` varchar(512) DEFAULT NULL,
  `Description` mediumtext,
  `Description_Text` mediumtext,
  `Description_Code` mediumtext,
  `Type` varchar(128) DEFAULT NULL,
  `Priority` varchar(128) DEFAULT NULL,
  `Status` varchar(128) DEFAULT NULL,
  `Resolution` varchar(128) DEFAULT NULL,
  `Creation_Date` datetime DEFAULT NULL,
  `Estimation_Date` datetime DEFAULT NULL,
  `Resolution_Date` datetime DEFAULT NULL,
  `Last_Updated` datetime DEFAULT NULL,
  `Story_Point` double DEFAULT NULL,
  `Timespent` double DEFAULT NULL,
  `In_Progress_Minutes` double DEFAULT NULL,
  `Total_Effort_Minutes` double DEFAULT NULL,
  `Resolution_Time_Minutes` double DEFAULT NULL,
  `Title_Changed_After_Estimation` tinyint DEFAULT NULL,
  `Description_Changed_After_Estimation` tinyint DEFAULT NULL,
  `Story_Point_Changed_After_Estimation` tinyint DEFAULT NULL,
  `Pull_Request_URL` varchar(512) DEFAULT NULL,
  `Creator_ID` int DEFAULT NULL,
  `Reporter_ID` int DEFAULT NULL,
  `Assignee_ID` int DEFAULT NULL,
  `Project_ID` int DEFAULT NULL,
  `Sprint_ID` int DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `Project_ID` (`Project_ID`),
  KEY `Assignee_ID` (`Assignee_ID`),
  KEY `Reporter_ID` (`Reporter_ID`),
  KEY `Sprint_ID` (`Sprint_ID`),
  KEY `P_Key` (`ID`),
  KEY `F_Key` (`Creator_ID`,`Reporter_ID`,`Assignee_ID`,`Project_ID`,`Sprint_ID`),
  CONSTRAINT `issue_ibfk_1` FOREIGN KEY (`Project_ID`) REFERENCES `Project` (`ID`),
  CONSTRAINT `issue_ibfk_2` FOREIGN KEY (`Assignee_ID`) REFERENCES `User` (`ID`),
  CONSTRAINT `issue_ibfk_3` FOREIGN KEY (`Reporter_ID`) REFERENCES `User` (`ID`),
  CONSTRAINT `issue_ibfk_4` FOREIGN KEY (`Sprint_ID`) REFERENCES `Sprint` (`ID`),
  CONSTRAINT `issue_ibfk_5` FOREIGN KEY (`Creator_ID`) REFERENCES `User` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
INSERT INTO `Issue` VALUES (3622,48861,'XD-161','https://jira.spring.io/rest/api/2/issue/48861','\"Add HTTP Delete Stream Operation\"','','','','Story','Minor','Done','Complete','2013-05-30 16:21:52','2013-05-30 15:21:52','2013-06-03 15:31:24','2013-06-11 23:46:14',5,NULL,5709,5709,5709,1,0,0,'',82,82,82,1,62);
INSERT INTO `Issue` VALUES (3628,48852,'XD-155','https://jira.spring.io/rest/api/2/issue/48852','\"Add a groovy script processor module\"','\"A processor module that accepts either the location of a groovy script resource or an inline script (string). Also some discussion about a default classpath location for scripts. \"','\"\"\"A processor module that accepts either the location of a groovy script resource or an inline script (string). Also some discussion about a default classpath location for scripts. \"\"\"','','Story','Minor','Done','Complete','2013-05-30 10:26:01','2013-05-30 09:26:01','2013-06-03 21:09:14','2013-06-11 23:46:07',5,NULL,4758,4758,6403,0,0,0,'',89,89,240,1,62);
INSERT INTO `Issue` VALUES (3630,48848,'XD-153','https://jira.spring.io/rest/api/2/issue/48848','\"create a gauge module\"','\"Spring config for simple gauge plus message handler to process message. There is some code common to RichGaugeHandler to coerce the payload to a double that should be refactored for reuse.\"','\"\"\"Spring config for simple gauge plus message handler to process message. There is some code common to RichGaugeHandler to coerce the payload to a double that should be refactored for reuse.\"\"\"','','Story','Minor','Done','Complete','2013-05-30 08:26:07','2013-05-30 07:26:07','2013-06-02 10:11:49','2013-06-11 23:46:16',5,NULL,2925,2925,4425,0,0,0,'',89,89,222,1,62);
INSERT INTO `Issue` VALUES (3631,48847,'XD-152','https://jira.spring.io/rest/api/2/issue/48847','\"Create rich gauge module\"','\"Spring config for rich gauge plus message handler to coerce a numeric or string payload to a double.\"','\"\"\"Spring config for rich gauge plus message handler to coerce a numeric or string payload to a double.\"\"\"','','Story','Minor','Done','Complete','2013-05-30 08:23:50','2013-05-30 07:23:50','2013-05-30 09:29:36','2013-06-11 23:46:06',5,NULL,0,0,65,0,0,0,'',89,89,89,1,62);
INSERT INTO `Issue` VALUES (3634,48833,'XD-149','https://jira.spring.io/rest/api/2/issue/48833','\"Create asciidoc toolchain script to create a \'toc2\' style html output\"','\"Publishing an html version of the guide that uses the \'toc2\' style format, table of contents on the left.  Looks like a \'stylesheet factory\' http://asciidoctor.org/docs/produce-custom-themes-using-asciidoctor-stylesheet-factory/  needs to be installed.  From the theme showcase, http://themes.asciidoctor.org/preview/, the \'golo\' theme has a toc2 style.  In the root of the git repo for the wiki is a build.gradle file that uses the asciidoctor gradle plugin, but it doesn\'t support using a single file with import as input. (See See https://github.com/asciidoctor/asciidoctor-gradle-plugin/issues/15 )  The mvn plugin does support this, so maybe using mvn is an option or just a bash script.\"','\"\"\"Publishing an html version of the guide that uses the \'toc2\' style format, table of contents on the left.  Looks like a \'stylesheet factory\' http://asciidoctor.org/docs/produce-custom-themes-using-asciidoctor-stylesheet-factory/  needs to be installed.  From the theme showcase, http://themes.asciidoctor.org/preview/, the \'golo\' theme has a toc2 style.  In the root of the git repo for the wiki is a build.gradle file that uses the asciidoctor gradle plugin, but it doesn\'t support using a single file with import as input. (See See https://github.com/asciidoctor/asciidoctor-gradle-plugin/issues/15 )  The mvn plugin does support this, so maybe using mvn is an option or just a bash script.\"\"\"','','Story','Minor','Done','Complete','2013-05-29 20:39:06','2013-05-29 19:39:06','2013-05-30 15:36:25','2013-06-11 23:46:14',4,NULL,199,199,1137,0,0,0,'',72,72,240,1,62);
INSERT INTO `Issue` VALUES (3635,48831,'XD-148','https://jira.spring.io/rest/api/2/issue/48831','\"Improve User Experience when Redis is not running\"','\"Redis is not running we get a nasty stacktrace:  {code} ~/dev/git/spring-xd/dist/spring-xd/xd/bin (master)] ➔ ./xd-container  13/05/29 16:17:15 INFO support.ClassPathXmlApplicationContext: Refreshing org.springframework.context.support.ClassPathXmlApplicationContext@851052d: startup date [Wed May 29 16:17:15 EDT 2013]; root of context hierarchy 13/05/29 16:17:16 INFO xml.XmlBeanDefinitionReader: Loading XML bean definitions from class path resource [META-INF/spring/launcher.xml] 13/05/29 16:17:16 INFO xml.XmlBeanDefinitionReader: Loading XML bean definitions from class path resource [META-INF/spring/redis.xml] 13/05/29 16:17:17 INFO support.DefaultListableBeanFactory: Pre-instantiating singletons in org.springframework.beans.factory.support.DefaultListableBeanFactory@4934ce4a: defining beans [org.springframework.context.support.PropertySourcesPlaceholderConfigurer#0,redisConnectionFactory,org.springframework.xd.dirt.launcher.RedisContainerLauncher#0]; root of factory hierarchy 13/05/29 16:17:17 INFO support.DefaultListableBeanFactory: Destroying singletons in org.springframework.beans.factory.support.DefaultListableBeanFactory@4934ce4a: defining beans [org.springframework.context.support.PropertySourcesPlaceholderConfigurer#0,redisConnectionFactory,org.springframework.xd.dirt.launcher.RedisContainerLauncher#0]; root of factory hierarchy Exception in thread \"\"main\"\" org.springframework.beans.factory.BeanCreationException: Error creating bean with name \'redisConnectionFactory\' defined in class path resource [META-INF/spring/redis.xml]: Invocation of init method failed; nested exception is com.lambdaworks.redis.RedisException: Unable to connect  at org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory.initializeBean(AbstractAutowireCapableBeanFactory.java:1488)  at org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory.doCreateBean(AbstractAutowireCapableBeanFactory.java:524)  at org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory.createBean(AbstractAutowireCapableBeanFactory.java:461)  at org.springframework.beans.factory.support.AbstractBeanFactory$1.getObject(AbstractBeanFactory.java:295)  at org.springframework.beans.factory.support.DefaultSingletonBeanRegistry.getSingleton(DefaultSingletonBeanRegistry.java:223)  at org.springframework.beans.factory.support.AbstractBeanFactory.doGetBean(AbstractBeanFactory.java:292)  at org.springframework.beans.factory.support.AbstractBeanFactory.getBean(AbstractBeanFactory.java:194)  at org.springframework.beans.factory.support.DefaultListableBeanFactory.preInstantiateSingletons(DefaultListableBeanFactory.java:626)  at org.springframework.context.support.AbstractApplicationContext.finishBeanFactoryInitialization(AbstractApplicationContext.java:932)  at org.springframework.context.support.AbstractApplicationContext.refresh(AbstractApplicationContext.java:479)  at org.springframework.context.support.ClassPathXmlApplicationContext.<init>(ClassPathXmlApplicationContext.java:139)  at org.springframework.context.support.ClassPathXmlApplicationContext.<init>(ClassPathXmlApplicationContext.java:83)  at org.springframework.xd.dirt.launcher.RedisContainerLauncher.main(RedisContainerLauncher.java:68)  at org.springframework.xd.ContainerMain.main(ContainerMain.java:68) Caused by: com.lambdaworks.redis.RedisException: Unable to connect  at com.lambdaworks.redis.RedisClient.connect(RedisClient.java:176)  at com.lambdaworks.redis.RedisClient.connectAsync(RedisClient.java:139)  at org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory.initConnection(LettuceConnectionFactory.java:108)  at org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory.afterPropertiesSet(LettuceConnectionFactory.java:86)  at org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory.invokeInitMethods(AbstractAutowireCapableBeanFactory.java:1547)  at org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory.initializeBean(AbstractAutowireCapableBeanFactory.java:1485)  ... 13 more Caused by: java.net.ConnectException: Connection refused: localhost/127.0.0.1:6379  at sun.nio.ch.SocketChannelImpl.checkConnect(Native Method)  at sun.nio.ch.SocketChannelImpl.finishConnect(SocketChannelImpl.java:599)  at org.jboss.netty.channel.socket.nio.NioClientBoss.connect(NioClientBoss.java:150)  at org.jboss.netty.channel.socket.nio.NioClientBoss.processSelectedKeys(NioClientBoss.java:105)  at org.jboss.netty.channel.socket.nio.NioClientBoss.process(NioClientBoss.java:79)  at org.jboss.netty.channel.socket.nio.AbstractNioSelector.run(AbstractNioSelector.java:312)  at org.jboss.netty.channel.socket.nio.NioClientBoss.run(NioClientBoss.java:42)  at java.util.concurrent.ThreadPoolExecutor$Worker.runTask(ThreadPoolExecutor.java:895)  at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:918)  at java.lang.Thread.run(Thread.java:680) {code}  I think it would be helpful to provide users with some helpful advice e.g.:  Redis does not seem to be running at \'localhost/127.0.0.1:6379\'. Did you start or install Redis? Please see for further help http://foo/bar   \"','\"\"\"Redis is not running we get a nasty stacktrace:    I think it would be helpful to provide users with some helpful advice e.g.:  Redis does not seem to be running at \'localhost/127.0.0.1:6379\'. Did you start or install Redis? Please see for further help http://foo/bar   \"\"\"','\" ~/dev/git/spring-xd/dist/spring-xd/xd/bin (master)] ➔ ./xd-container  13/05/29 16:17:15 INFO support.ClassPathXmlApplicationContext: Refreshing org.springframework.context.support.ClassPathXmlApplicationContext@851052d: startup date [Wed May 29 16:17:15 EDT 2013]; root of context hierarchy 13/05/29 16:17:16 INFO xml.XmlBeanDefinitionReader: Loading XML bean definitions from class path resource [META-INF/spring/launcher.xml] 13/05/29 16:17:16 INFO xml.XmlBeanDefinitionReader: Loading XML bean definitions from class path resource [META-INF/spring/redis.xml] 13/05/29 16:17:17 INFO support.DefaultListableBeanFactory: Pre-instantiating singletons in org.springframework.beans.factory.support.DefaultListableBeanFactory@4934ce4a: defining beans [org.springframework.context.support.PropertySourcesPlaceholderConfigurer#0,redisConnectionFactory,org.springframework.xd.dirt.launcher.RedisContainerLauncher#0]; root of factory hierarchy 13/05/29 16:17:17 INFO support.DefaultListableBeanFactory: Destroying singletons in org.springframework.beans.factory.support.DefaultListableBeanFactory@4934ce4a: defining beans [org.springframework.context.support.PropertySourcesPlaceholderConfigurer#0,redisConnectionFactory,org.springframework.xd.dirt.launcher.RedisContainerLauncher#0]; root of factory hierarchy Exception in thread \"\"\"\"main\"\"\"\" org.springframework.beans.factory.BeanCreationException: Error creating bean with name \'redisConnectionFactory\' defined in class path resource [META-INF/spring/redis.xml]: Invocation of init method failed; nested exception is com.lambdaworks.redis.RedisException: Unable to connect  at org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory.initializeBean(AbstractAutowireCapableBeanFactory.java:1488)  at org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory.doCreateBean(AbstractAutowireCapableBeanFactory.java:524)  at org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory.createBean(AbstractAutowireCapableBeanFactory.java:461)  at org.springframework.beans.factory.support.AbstractBeanFactory$1.getObject(AbstractBeanFactory.java:295)  at org.springframework.beans.factory.support.DefaultSingletonBeanRegistry.getSingleton(DefaultSingletonBeanRegistry.java:223)  at org.springframework.beans.factory.support.AbstractBeanFactory.doGetBean(AbstractBeanFactory.java:292)  at org.springframework.beans.factory.support.AbstractBeanFactory.getBean(AbstractBeanFactory.java:194)  at org.springframework.beans.factory.support.DefaultListableBeanFactory.preInstantiateSingletons(DefaultListableBeanFactory.java:626)  at org.springframework.context.support.AbstractApplicationContext.finishBeanFactoryInitialization(AbstractApplicationContext.java:932)  at org.springframework.context.support.AbstractApplicationContext.refresh(AbstractApplicationContext.java:479)  at org.springframework.context.support.ClassPathXmlApplicationContext.<init>(ClassPathXmlApplicationContext.java:139)  at org.springframework.context.support.ClassPathXmlApplicationContext.<init>(ClassPathXmlApplicationContext.java:83)  at org.springframework.xd.dirt.launcher.RedisContainerLauncher.main(RedisContainerLauncher.java:68)  at org.springframework.xd.ContainerMain.main(ContainerMain.java:68) Caused by: com.lambdaworks.redis.RedisException: Unable to connect  at com.lambdaworks.redis.RedisClient.connect(RedisClient.java:176)  at com.lambdaworks.redis.RedisClient.connectAsync(RedisClient.java:139)  at org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory.initConnection(LettuceConnectionFactory.java:108)  at org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory.afterPropertiesSet(LettuceConnectionFactory.java:86)  at org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory.invokeInitMethods(AbstractAutowireCapableBeanFactory.java:1547)  at org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory.initializeBean(AbstractAutowireCapableBeanFactory.java:1485)  ... 13 more Caused by: java.net.ConnectException: Connection refused: localhost/127.0.0.1:6379  at sun.nio.ch.SocketChannelImpl.checkConnect(Native Method)  at sun.nio.ch.SocketChannelImpl.finishConnect(SocketChannelImpl.java:599)  at org.jboss.netty.channel.socket.nio.NioClientBoss.connect(NioClientBoss.java:150)  at org.jboss.netty.channel.socket.nio.NioClientBoss.processSelectedKeys(NioClientBoss.java:105)  at org.jboss.netty.channel.socket.nio.NioClientBoss.process(NioClientBoss.java:79)  at org.jboss.netty.channel.socket.nio.AbstractNioSelector.run(AbstractNioSelector.java:312)  at org.jboss.netty.channel.socket.nio.NioClientBoss.run(NioClientBoss.java:42)  at java.util.concurrent.ThreadPoolExecutor$Worker.runTask(ThreadPoolExecutor.java:895)  at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:918)  at java.lang.Thread.run(Thread.java:680) \"','Story','Minor','Done','Complete','2013-05-29 14:22:54','2013-05-29 13:22:54','2013-05-31 16:59:44','2013-06-11 23:46:13',2,NULL,1502,1502,3036,0,0,0,'',93,93,240,1,62);
INSERT INTO `Issue` VALUES (3640,48791,'XD-143','https://jira.spring.io/rest/api/2/issue/48791','\"Create externalized property file to support connectivity to redis\"','\"We need to have an externalized property file(under xd/conf/) for the xd-container & admin scripts to use as options. \"','\"\"\"We need to have an externalized property file(under xd/conf/) for the xd-container & admin scripts to use as options. \"\"\"','','Story','Minor','Done','Complete','2013-05-28 16:26:55','2013-05-28 15:26:55','2013-06-05 09:47:52','2013-06-11 23:46:12',3,NULL,11082,11082,11120,1,0,0,'',91,91,91,1,62);
INSERT INTO `Issue` VALUES (3643,48780,'XD-140','https://jira.spring.io/rest/api/2/issue/48780','\"Parameterize syslog Source; Add Support for TCP\"','\"The syslog source currently is hard-coded to use udp on port 11111.  Need to parameterize the port and provide an option to use TCP.\"','\"\"\"The syslog source currently is hard-coded to use udp on port 11111.  Need to parameterize the port and provide an option to use TCP.\"\"\"','','Story','Minor','Done','Complete','2013-05-28 12:32:46','2013-05-28 11:32:46','2013-05-28 16:30:12','2013-06-11 23:46:17',2,NULL,237,237,237,0,0,0,'',82,82,82,1,62);
INSERT INTO `Issue` VALUES (3644,48770,'XD-139','https://jira.spring.io/rest/api/2/issue/48770','\"Update README.txt to include instructions on how to build\"','\"Building XD should not be part of the out first out of the box experience, but we should include some instructions on what targets are available, such as distXD.\"','\"\"\"Building XD should not be part of the out first out of the box experience, but we should include some instructions on what targets are available, such as distXD.\"\"\"','','Story','Minor','Done','Complete','2013-05-28 11:33:27','2013-05-28 10:33:27','2013-05-28 14:26:50','2013-06-11 23:46:16',2,NULL,93,93,173,0,0,0,'',72,72,91,1,62);
INSERT INTO `Issue` VALUES (3645,48766,'XD-138','https://jira.spring.io/rest/api/2/issue/48766','\"Prepare blog post for M1\"','','','','Story','Minor','Done','Complete','2013-05-28 11:20:13','2013-05-28 10:20:13','2013-06-10 13:39:37','2013-06-11 23:46:04',5,NULL,5988,5988,18859,0,0,0,'',72,72,72,1,62);
INSERT INTO `Issue` VALUES (3646,48765,'XD-137','https://jira.spring.io/rest/api/2/issue/48765','\"Release Spring XD 1.0 M1\"','','','','Story','Minor','Done','Complete','2013-05-28 11:04:56','2013-05-28 10:04:56','2013-06-17 08:41:45','2013-08-14 14:20:17',5,NULL,9781,9781,28656,0,0,1,'',72,72,72,1,62);
INSERT INTO `Issue` VALUES (3647,48764,'XD-136','https://jira.spring.io/rest/api/2/issue/48764','\"Documentation that points on how to install hadoop\"','\"Pointers to other documentation on how to install hadoop. \"','\"\"\"Pointers to other documentation on how to install hadoop. \"\"\"','','Story','Minor','Done','Complete','2013-05-28 11:03:29','2013-05-28 10:03:29','2013-05-30 11:16:09','2013-06-11 23:46:17',3,NULL,55,55,2892,0,0,0,'',72,72,222,1,62);
INSERT INTO `Issue` VALUES (3648,48763,'XD-135','https://jira.spring.io/rest/api/2/issue/48763','\"Documentation on XD Architecture\"','\"Show overall flow of data in a stream, the server components \'admin\' and \'container\'.  How modules are deployed.\"','\"\"\"Show overall flow of data in a stream, the server components \'admin\' and \'container\'.  How modules are deployed.\"\"\"','','Story','Minor','Done','Complete','2013-05-28 11:02:56','2013-05-28 10:02:56','2013-06-06 00:12:23','2013-06-11 23:46:10',4,NULL,9625,9625,12309,0,0,0,'',72,72,72,1,62);
INSERT INTO `Issue` VALUES (3649,48762,'XD-134','https://jira.spring.io/rest/api/2/issue/48762','\"Investigate link checking tool for user guide\"','\"Asciidoc/doctor might have one as part of it toolchain\"','\"\"\"Asciidoc/doctor might have one as part of it toolchain\"\"\"','','Story','Minor','Done','Complete','2013-05-28 10:59:31','2013-05-28 09:59:31','2013-05-30 11:16:38','2013-06-11 23:46:09',2,NULL,1048,1048,2897,0,0,0,'',72,72,222,1,62);
INSERT INTO `Issue` VALUES (3650,48760,'XD-133','https://jira.spring.io/rest/api/2/issue/48760','\"Fail Sonar CI build if there are any package tangles violated.\"','\"Similar to what would show up on structure101 reports.\"','\"\"\"Similar to what would show up on structure101 reports.\"\"\"','','Story','Minor','Done','Complete','2013-05-28 10:53:20','2013-05-28 09:53:20','2013-05-28 12:56:55','2013-06-11 23:46:11',1,NULL,9,9,123,0,0,1,'',72,72,93,1,62);
INSERT INTO `Issue` VALUES (3652,48758,'XD-131','https://jira.spring.io/rest/api/2/issue/48758','\"Upgrade Lettuce to 2.3.2\"','','','','Story','Minor','Done','Complete','2013-05-28 10:42:14','2013-05-28 09:42:14','2013-05-28 16:19:31','2013-06-11 23:46:20',2,NULL,140,140,337,0,0,0,'',240,240,240,1,62);
INSERT INTO `Issue` VALUES (3653,48757,'XD-130','https://jira.spring.io/rest/api/2/issue/48757','\"Remove container entry in Redis when the application context event to shutdown the container is fired\"','','','','Story','Minor','Done','Complete','2013-05-28 10:42:08','2013-05-28 09:42:08','2013-05-30 09:10:51','2013-06-11 23:46:19',3,NULL,1335,1335,2788,0,0,0,'',72,72,240,1,62);
INSERT INTO `Issue` VALUES (3654,48756,'XD-129','https://jira.spring.io/rest/api/2/issue/48756','\"Documenation for building/starting redis servers\"','','','','Story','Minor','Done','Complete','2013-05-28 10:28:10','2013-05-28 09:28:10','2013-05-30 07:44:46','2013-06-11 23:46:06',2,NULL,1063,1063,2716,1,0,0,'',72,72,93,1,62);
INSERT INTO `Issue` VALUES (3655,48754,'XD-128','https://jira.spring.io/rest/api/2/issue/48754','\"Create TCP sink module\"','\"Based off SI tcp inbound adapter.  This will allow for event fowarding.\"','\"\"\"Based off SI tcp inbound adapter.  This will allow for event fowarding.\"\"\"','','Story','Minor','Done','Complete','2013-05-28 08:36:05','2013-05-28 07:36:05','2013-05-30 16:23:05','2013-06-11 23:46:13',3,NULL,1688,1688,3346,0,0,1,'',72,72,82,1,62);
INSERT INTO `Issue` VALUES (3656,48753,'XD-127','https://jira.spring.io/rest/api/2/issue/48753','\"Create TCP source module\"','\"Based off SI tcp inbound adapter.  This will allow for event forwarding that can select among the existing SI serialized/deserializer options. \"','\"\"\"Based off SI tcp inbound adapter.  This will allow for event forwarding that can select among the existing SI serialized/deserializer options. \"\"\"','','Story','Minor','Done','Complete','2013-05-28 08:35:42','2013-05-28 07:35:42','2013-05-29 22:46:12','2013-06-11 23:46:04',3,NULL,761,761,2290,0,0,1,'',72,72,82,1,62);
INSERT INTO `Issue` VALUES (3665,48703,'XD-118','https://jira.spring.io/rest/api/2/issue/48703','\"replace testsource with time and testsink with log\"','\"This should facilitate testing while avoiding any class dependencies. Also, log is a generally useful sink by itself and time is a more interesting source for testing (should accept --interval for the seconds between time messages).\"','\"\"\"This should facilitate testing while avoiding any class dependencies. Also, log is a generally useful sink by itself and time is a more interesting source for testing (should accept --interval for the seconds between time messages).\"\"\"','','Story','Minor','Done','Complete','2013-05-23 14:58:23','2013-05-23 13:58:23','2013-05-23 15:20:52','2013-06-11 23:46:05',1,NULL,22,22,22,0,0,0,'',110,110,110,1,63);
INSERT INTO `Issue` VALUES (3666,48701,'XD-117','https://jira.spring.io/rest/api/2/issue/48701','\"add spring-integration-groovy to container dependencies\"','\"This will enable the use of groovy scripts within modules.\"','\"\"\"This will enable the use of groovy scripts within modules.\"\"\"','','Story','Minor','Done','Complete','2013-05-23 13:36:27','2013-05-23 12:36:27','2013-05-23 13:45:54','2013-06-11 23:46:17',1,NULL,9,9,9,0,0,0,'',110,110,110,1,63);
INSERT INTO `Issue` VALUES (3667,48698,'XD-116','https://jira.spring.io/rest/api/2/issue/48698','\"add SpEL \'filter\' processor\"','\"It should provide an \'expression\' param for SpEL and have a default value of true (accept everything).\"','\"\"\"It should provide an \'expression\' param for SpEL and have a default value of true (accept everything).\"\"\"','','Story','Minor','Done','Complete','2013-05-23 13:17:39','2013-05-23 12:17:39','2013-05-23 13:34:02','2013-06-11 23:46:07',1,NULL,7,7,16,0,0,0,'',110,110,110,1,63);
INSERT INTO `Issue` VALUES (3668,48697,'XD-115','https://jira.spring.io/rest/api/2/issue/48697','\"add SpEL \'transform\' processor\"','\"It should provide an \'expression\' param for SpEL and have a default pass-thru of the payload.\"','\"\"\"It should provide an \'expression\' param for SpEL and have a default pass-thru of the payload.\"\"\"','','Story','Minor','Done','Complete','2013-05-23 13:16:37','2013-05-23 12:16:37','2013-05-23 13:33:49','2013-06-11 23:46:04',1,NULL,7,7,17,0,0,0,'',110,110,110,1,63);
INSERT INTO `Issue` VALUES (3669,48694,'XD-114','https://jira.spring.io/rest/api/2/issue/48694','\"Add install script for Redis\"','\"This assumes the redis source tar is available under $rootDir/redis/redis-2.6.13.tar.gz  The install script does the following:  - Check the platform OS & arch - unzip the tar, compile the sources\"','\"\"\"This assumes the redis source tar is available under $rootDir/redis/redis-2.6.13.tar.gz  The install script does the following:  - Check the platform OS & arch - unzip the tar, compile the sources\"\"\"','','Technical task','Minor','Done','Complete','2013-05-23 12:38:33','2013-05-23 11:38:33','2013-05-23 18:14:50','2013-06-11 23:46:13',2,NULL,0,0,336,0,0,0,'',91,91,247,1,63);
INSERT INTO `Issue` VALUES (3670,48691,'XD-112','https://jira.spring.io/rest/api/2/issue/48691','\"Update XD to Use SI 3.0.0.M2\"','','','','Story','Minor','Done','Complete','2013-05-23 11:15:10','2013-05-23 10:15:10','2013-05-24 13:39:23','2013-06-11 23:46:07',1,NULL,1583,1583,1584,0,0,0,'',82,82,110,1,63);
INSERT INTO `Issue` VALUES (3671,48689,'XD-111','https://jira.spring.io/rest/api/2/issue/48689','\"Create final distribution zip across multiple projects\"','\"The final directory structure should look like  <install-dir>/xd <install-dir>/redis <install-dir>/gemfire  inside the XD directory   /xd/bin - which has xd-container and xd-admin scripts /xd/lib  inside the gemfire directory /gemfire/bin - has the gemfire-server script /gemfire/lib   inside the redis directory is   /redis/redis-latest-v.x.y.z.tar /redis/README /readis/install-redis  - script that does the basic 4 commands to install redis.   There should be a gradle task that runs after the distZip task, that will take the contents of different project directories, script diretories and \'redis-binary\' directories and creates the final layout for the distribution.\"','\"\"\"The final directory structure should look like  <install-dir>/xd <install-dir>/redis <install-dir>/gemfire  inside the XD directory   /xd/bin - which has xd-container and xd-admin scripts /xd/lib  inside the gemfire directory /gemfire/bin - has the gemfire-server script /gemfire/lib   inside the redis directory is   /redis/redis-latest-v.x.y.z.tar /redis/README /readis/install-redis  - script that does the basic 4 commands to install redis.   There should be a gradle task that runs after the distZip task, that will take the contents of different project directories, script diretories and \'redis-binary\' directories and creates the final layout for the distribution.\"\"\"','','Story','Minor','Done','Complete','2013-05-23 09:39:54','2013-05-23 08:39:54','2013-05-24 13:28:26','2013-06-11 23:46:15',5,NULL,1319,1319,1668,0,0,0,'',72,72,91,1,63);
INSERT INTO `Issue` VALUES (3673,48684,'XD-109','https://jira.spring.io/rest/api/2/issue/48684','\"Documentation for starting Spring XD servers\"','','','','Story','Minor','Done','Complete','2013-05-23 02:06:01','2013-05-23 01:06:01','2013-05-28 10:27:46','2013-06-11 23:46:11',1,NULL,7701,7701,7701,1,0,0,'',72,72,72,1,63);
INSERT INTO `Issue` VALUES (3674,48683,'XD-108','https://jira.spring.io/rest/api/2/issue/48683','\"Build script should not package \'spring-xd-dirt\' scripts \"','\"We are packaging separate scripts to start XDAdmin and XDContainer.  The Gradle application plugin will generate an unwanted \'spring-xd-dirt\' scripts, this should be removed from the bin directory when creating a distribution zip.\"','\"\"\"We are packaging separate scripts to start XDAdmin and XDContainer.  The Gradle application plugin will generate an unwanted \'spring-xd-dirt\' scripts, this should be removed from the bin directory when creating a distribution zip.\"\"\"','','Story','Minor','Done','Complete','2013-05-23 01:27:49','2013-05-23 00:27:49','2013-05-24 13:36:51','2013-06-11 23:46:17',1,NULL,411,411,2169,0,0,0,'',72,72,91,1,63);
INSERT INTO `Issue` VALUES (3677,48680,'XD-105','https://jira.spring.io/rest/api/2/issue/48680','\"Add LICENSE to be included in root directory of distribution\"','\"should contain apache licence\"','\"\"\"should contain apache licence\"\"\"','','Story','Minor','Done','Complete','2013-05-23 00:38:49','2013-05-22 23:38:49','2013-05-24 14:20:04','2013-06-11 23:46:05',1,NULL,0,0,2261,0,0,0,'',72,72,91,1,63);
INSERT INTO `Issue` VALUES (3678,48679,'XD-104','https://jira.spring.io/rest/api/2/issue/48679','\"Add README to be included in root directory of distribution\"','\"should explain basic layout of the distribution\"','\"\"\"should explain basic layout of the distribution\"\"\"','','Story','Minor','Done','Complete','2013-05-23 00:37:44','2013-05-22 23:37:44','2013-05-24 14:19:47','2013-06-11 23:46:06',1,NULL,27,27,2262,0,0,0,'',72,72,91,1,63);
INSERT INTO `Issue` VALUES (3679,48678,'XD-103','https://jira.spring.io/rest/api/2/issue/48678','\"Create XDAdmin server to start container launcher\"','\"This will launch the RedisContainerLauncher, in future will be able to select from a variety of middleware options.\"','\"\"\"This will launch the RedisContainerLauncher, in future will be able to select from a variety of middleware options.\"\"\"','','Story','Minor','Done','Complete','2013-05-22 23:37:24','2013-05-22 22:37:24','2013-05-23 01:31:17','2013-06-11 23:46:09',1,NULL,2,2,113,0,0,0,'',72,72,72,1,63);
INSERT INTO `Issue` VALUES (3680,48677,'XD-102','https://jira.spring.io/rest/api/2/issue/48677','\"Create XDContainer class to start stream server\"','\"Provide optional command line arg to embed the container launcher, aka - xd-admin server.    XDContainer.sh --embeddAdmin\"','\"\"\"Provide optional command line arg to embed the container launcher, aka - xd-admin server.    XDContainer.sh --embeddAdmin\"\"\"','','Story','Minor','Done','Complete','2013-05-22 23:35:27','2013-05-22 22:35:27','2013-05-23 01:31:11','2013-06-11 23:46:09',1,NULL,100,100,115,1,0,0,'',72,72,72,1,63);
INSERT INTO `Issue` VALUES (3681,48673,'XD-101','https://jira.spring.io/rest/api/2/issue/48673','\"Add gradle tasks that build and bundle the redis server\"','','','','Technical task','Minor','Done','Invalid','2013-05-22 12:18:41','2013-05-22 11:18:41','2013-05-24 15:03:32','2013-06-11 23:46:13',2,NULL,3039,3039,3044,1,0,0,'',91,91,91,1,63);
INSERT INTO `Issue` VALUES (3683,48655,'XD-99','https://jira.spring.io/rest/api/2/issue/48655','\"Sonar build is failing\"','\"https://build.springsource.org/browse/XD-SONAR-34  Caused by: java.lang.ClassNotFoundException: org.sonar.api.Plugin         at org.codehaus.plexus.classworlds.strategy.SelfFirstStrategy.loadClass(SelfFirstStrategy.java:50)         at org.codehaus.plexus.classworlds.realm.ClassRealm.loadClass(ClassRealm.java:244)         at org.codehaus.plexus.classworlds.realm.ClassRealm.loadClass(ClassRealm.java:230)         ... 94 more\"','\"\"\"https://build.springsource.org/browse/XD-SONAR-34  Caused by: java.lang.ClassNotFoundException: org.sonar.api.Plugin         at org.codehaus.plexus.classworlds.strategy.SelfFirstStrategy.loadClass(SelfFirstStrategy.java:50)         at org.codehaus.plexus.classworlds.realm.ClassRealm.loadClass(ClassRealm.java:244)         at org.codehaus.plexus.classworlds.realm.ClassRealm.loadClass(ClassRealm.java:230)         ... 94 more\"\"\"','','Story','Minor','Done','Complete','2013-05-20 22:29:03','2013-05-20 21:29:03','2013-05-21 08:34:54','2013-06-11 23:46:19',1,NULL,0,0,605,0,0,0,'',72,72,93,1,63);
INSERT INTO `Issue` VALUES (3684,48653,'XD-98','https://jira.spring.io/rest/api/2/issue/48653','\"Documentation on the module system and how to contribute new modules\"','\"For people who are familiar with Spring/Spring Integration provide documents that show how to add additional input sources/sinks.\"','\"\"\"For people who are familiar with Spring/Spring Integration provide documents that show how to add additional input sources/sinks.\"\"\"','','Story','Minor','Done','Complete','2013-05-20 17:08:21','2013-05-20 16:08:21','2013-05-27 11:55:35','2013-06-11 23:46:20',3,NULL,0,0,9767,0,0,0,'',72,72,89,1,63);
INSERT INTO `Issue` VALUES (3691,48643,'XD-91','https://jira.spring.io/rest/api/2/issue/48643','\"Documentation for field value taps\"','\"Put on the guide as a section in an \'input-stream\' wiki page.   \"','\"\"\"Put on the guide as a section in an \'input-stream\' wiki page.   \"\"\"','','Story','Minor','Done','Complete','2013-05-20 11:02:15','2013-05-20 10:02:15','2013-05-27 11:55:29','2013-06-11 23:46:12',3,NULL,0,0,10133,0,0,0,'',72,72,89,1,63);
INSERT INTO `Issue` VALUES (3694,48640,'XD-88','https://jira.spring.io/rest/api/2/issue/48640','\"Documentation for counter taps\"','\"Put on the guide as a section in an \'input-stream\' wiki page.   \"','\"\"\"Put on the guide as a section in an \'input-stream\' wiki page.   \"\"\"','','Story','Minor','Done','Complete','2013-05-20 11:01:44','2013-05-20 10:01:44','2013-05-28 09:05:49','2013-06-11 23:46:11',3,NULL,113,113,11404,0,0,0,'',72,72,89,1,63);
INSERT INTO `Issue` VALUES (3696,48638,'XD-86','https://jira.spring.io/rest/api/2/issue/48638','\"Documentation for \"\"twittersearch | file\"\" processing\"','\"Put on the guide as a section in an \'input-stream\' wiki page.   \"','\"\"\"Put on the guide as a section in an \'input-stream\' wiki page.   \"\"\"','','Story','Minor','Done','Complete','2013-05-20 11:00:54','2013-05-20 10:00:54','2013-05-24 14:45:56','2013-06-11 23:46:15',3,NULL,22,22,5985,0,0,0,'',72,72,84,1,63);
INSERT INTO `Issue` VALUES (3697,48637,'XD-85','https://jira.spring.io/rest/api/2/issue/48637','\"Documentation for \"\"gemfirecq | file\"\" processing\"','\"Put on the guide as a section in an \'input-stream\' wiki page.   \"','\"\"\"Put on the guide as a section in an \'input-stream\' wiki page.   \"\"\"','','Story','Minor','Done','Complete','2013-05-20 11:00:37','2013-05-20 10:00:37','2013-05-27 11:55:07','2013-06-11 23:46:13',3,NULL,0,0,10134,0,0,0,'',72,72,89,1,63);

DROP TABLE IF EXISTS `Issue_Component`;
CREATE TABLE `Issue_Component` (
  `Issue_ID` int DEFAULT NULL,
  `Component_ID` int DEFAULT NULL,
  KEY `Component_ID` (`Component_ID`),
  KEY `F_Key` (`Issue_ID`,`Component_ID`),
  CONSTRAINT `issue_component_ibfk_1` FOREIGN KEY (`Component_ID`) REFERENCES `Component` (`ID`),
  CONSTRAINT `issue_component_ibfk_2` FOREIGN KEY (`Issue_ID`) REFERENCES `Issue` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `Issue_Link`;
CREATE TABLE `Issue_Link` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Issue_ID` int DEFAULT NULL,
  `Name` varchar(512) DEFAULT NULL,
  `Description` varchar(2048) DEFAULT NULL,
  `Direction` varchar(45) DEFAULT NULL,
  `Target_Issue_ID` int DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `Target_Issue_ID` (`Target_Issue_ID`),
  KEY `P_Key` (`ID`),
  KEY `issue_link_ibfk_3` (`Issue_ID`),
  CONSTRAINT `issue_link_ibfk_2` FOREIGN KEY (`Target_Issue_ID`) REFERENCES `Issue` (`ID`),
  CONSTRAINT `issue_link_ibfk_3` FOREIGN KEY (`Issue_ID`) REFERENCES `Issue` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `Project`;
CREATE TABLE `Project` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Project_Key` varchar(128) DEFAULT NULL,
  `Name` varchar(512) DEFAULT NULL,
  `URL` varchar(512) DEFAULT NULL,
  `Description` varchar(2048) DEFAULT NULL,
  `Start_Date` datetime DEFAULT NULL,
  `Last_Update_Date` datetime DEFAULT NULL,
  `SP_Field_ID` varchar(45) DEFAULT NULL,
  `Repository_ID` int DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `P_Key` (`ID`),
  KEY `F_Key` (`Repository_ID`),
  CONSTRAINT `project_ibfk_1` FOREIGN KEY (`Repository_ID`) REFERENCES `Repository` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
INSERT INTO `Project` VALUES (1,'XD','Spring XD','https://jira.spring.io/projects/XD/','Spring XD makes it easy to solve common big data problems such as data ingestion and export, real-time analytics, and batch workflow orchestration','2013-04-12 06:37:17','2018-11-20 15:18:11','customfield_10142',1);

DROP TABLE IF EXISTS `Repository`;
CREATE TABLE `Repository` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Name` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `Description` varchar(2048) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `URL` varchar(512) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `P_Key` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
INSERT INTO `Repository` VALUES (1,'Spring','The Spring Framework is an application framework and inversion of control container for the Java platform. The framework\'s core features can be used by any Java application, but there are extensions for building web applications on top of the Java EE (Enterprise Edition) platform. ','https://jira.spring.io/');

DROP TABLE IF EXISTS `Sprint`;
CREATE TABLE `Sprint` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `JiraID` int DEFAULT NULL,
  `Name` varchar(512) DEFAULT NULL,
  `State` varchar(512) DEFAULT NULL,
  `Start_Date` datetime DEFAULT NULL,
  `End_Date` datetime DEFAULT NULL,
  `Activated_Date` datetime DEFAULT NULL,
  `Complete_Date` datetime DEFAULT NULL,
  `Project_ID` int DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `P_Key` (`ID`),
  KEY `F_Key` (`Project_ID`),
  CONSTRAINT `sprint_ibfk_1` FOREIGN KEY (`Project_ID`) REFERENCES `Project` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
INSERT INTO `Sprint` VALUES (63,5,'Sprint 4','CLOSED','2013-05-20 17:05:45','2013-05-24 17:05:45',NULL,'2013-05-28 16:30:54',1);
INSERT INTO `Sprint` VALUES (62,6,'Sprint 5','CLOSED','2013-05-28 17:25:33','2013-06-03 17:25:33',NULL,'2013-06-03 16:40:13',1);

DROP TABLE IF EXISTS `User`;
CREATE TABLE `User` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Project_ID` int DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `P_Key` (`ID`),
  KEY `F_Key` (`Project_ID`),
  CONSTRAINT `user_ibfk_1` FOREIGN KEY (`Project_ID`) REFERENCES `Project` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
INSERT INTO `User` VALUES (72,1);
INSERT INTO `User` VALUES (82,1);
INSERT INTO `User` VALUES (84,1);
INSERT INTO `User` VALUES (89,1);
INSERT INTO `User` VALUES (91,1);
INSERT INTO `User` VALUES (93,1);
INSERT INTO `User` VALUES (110,1);
INSERT INTO `User` VALUES (222,1);
INSERT INTO `User` VALUES (240,1);
INSERT INTO `User` VALUES (247,1);

DROP TABLE IF EXISTS `Version`;
CREATE TABLE `Version` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Jira_ID` int DEFAULT NULL,
  `Name` varchar(512) DEFAULT NULL,
  `Description` varchar(2048) DEFAULT NULL,
  `Archived` tinyint DEFAULT NULL,
  `Released` tinyint DEFAULT NULL,
  `Release_Date` datetime DEFAULT NULL,
  `Project_ID` int DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `P_Key` (`ID`),
  KEY `F_Key` (`Project_ID`),
  CONSTRAINT `version_ibfk_1` FOREIGN KEY (`Project_ID`) REFERENCES `Project` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=1;
